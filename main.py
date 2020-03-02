import subprocess
import tempfile
from os import path, environ, stat
from typing import Tuple, Any
import json

import boto3

storage = boto3.client('s3', endpoint_url='https://storage.yandexcloud.net/')

def parse_event(event: dict) -> Tuple[str, str]:
    message = event['messages'][0]
    return message['details']['bucket_id'], message['details']['object_id']


def clamav_scan(fname):
    dname = path.dirname(fname)
    out = subprocess.check_output(
        ['/function/code/clamav/clamscan', '--gen-json=yes', '--database=/function/code/clamav/cvd', fname],
        env={
            'LD_LIBRARY_PATH': '/function/code/clamav'
        },
        cwd=dname
    ).decode('utf-8')

    # --gen-json doesn't work in clamav, so we'll parse raw output
    result = {
        'scanned': 0,
        'infected': 0,
        'known_viruses': 0,
    }
    for line in out.split("\n"):
        line = line.strip()
        if line.startswith("---"):
            continue

        parts = [i.strip() for i in line.split(":")]
        if parts[0] == 'Infected files':
            result['infected'] = int(parts[1])
        if parts[0] == 'Scanned files':
            result['scanned'] = int(parts[1])
        if parts[0] == 'Known viruses':
            result['known_viruses'] = int(parts[1])

    return result


def notify_infected(result, bucket: str, obj: str) -> dict:
    body = json.dumps({
        'object': {
            'bucket': bucket,
            'object': obj,
        },
        'result': result,
    })
    # TODO write your custom notification here, raise exception if failed, it will be retried externally
    print('notify infected {}'.format(body))


def handler(event: dict, context: dict) -> Any:
    bucket, obj = parse_event(event)

    if not bucket or not obj:
        raise Exception('no object and/or bucket in event')

    with tempfile.NamedTemporaryFile() as f:
        print('downloading {}/{} to {}'.format(bucket, obj, f.name))
        storage.download_fileobj(bucket, obj, f)
        f.flush()
        size = stat(f.name).st_size
        print('downloaded {}/{} to {} (size={})'.format(bucket, obj, f.name, size))

        print('scanning {}'.format(f.name))
        result = clamav_scan(f.name)
        print('finished scanning {}'.format(f.name))

        if result['scanned'] != 1:
            raise Exception('no files were scanned')
        if result['infected'] != 0:
            notify_infected(result, bucket, obj)

        return result

