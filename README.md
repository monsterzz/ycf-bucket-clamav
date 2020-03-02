## Yandex Cloud Functions / ClamAV file scanner

This example shows how to check all created and updated files in Yandex Object Storage with ClamAV.

TODO:

[ ] Write your own notification rules (`notify_infected` in `main.py`). 

### ClamAV

We need to get statically built binaries for ClamAV. If you're comfortable with pre-built binaries - just grab `monsterzz/clamav-static:latest` from Docker Hub.
If you want to build it by yourself — use `clamav/Dockerfile` (`docker build -t monsterzz/clamav-static:latest .`).

### ClamAV Database

Newest version of database will be downloaded and packaged to Cloud Functions deployment package.
To update databases — just rebuild package using `make all` and deploy it.

### Pre-requisites

To deploy and run Cloud Functions you need to have CLI (`yc`) installed and configured. Refer to platform documentation
for detailed guide.

First of all, we need to create Service Account to access Object Storage from Cloud Function:

    $ yc iam service-account create --name clamav
    id: aje00000000000000000
    folder_id: b1g00000000000000000
    created_at: "2020-03-02T21:15:19Z"
    name: clamav
    
Then, grant required roles to this account:

    $ yc resource-manager folder add-access-binding <FOLDER-NAME> \
         --subject serviceAccount:aje00000000000000000 \
         --role viewer
    $ yc resource-manager folder add-access-binding <FOLDER-NAME> \
         --subject serviceAccount:aje00000000000000000 \
         --role serverless.functions.invoker

And last but not the least, we need to issue static credentials to access AWS Compatible APIs:

    $ yc iam access-key create --service-account-name clamav-guide
    access_key:
      id: aje00000000000000000
      service_account_id: aje00000000000000000
      created_at: "2020-03-02T18:24:04Z"
      key_id: MKkh9Y0fzIV6Jm3gSJ__
    secret: XXXXXXXXXXXXXXXXXXXXXXX
    
**Write down you secret, it won't show again**

### Yandex Cloud Functions

Be sure to build latest version of deployment package (use `make all` to produce `dist.zip`).
Then create Object Storage bucket and upload this package (use web console to do that, that's pretty easy).
Write down bucket and object name and create new function:

    $ yc serverless function create --name clamav-scanner
    done (1s)
    id: d4e00000000000000000
    folder_id: b1g00000000000000000
    created_at: "2020-03-02T18:26:59.866Z"
    name: clamav-scanner
    log_group_id: ckg00000000000000000
    http_invoke_url: https://functions.yandexcloud.net/d4e00000000000000000
    status: ACTIVE

Then you need to create new version:

    $ yc serverless function version create --function-name clamav-scanner \
        --runtime python37 \
        --entrypoint main.handler \
        --memory 512MB \
        --execution-timeout 60s \
        --environment AWS_ACCESS_KEY_ID=<YOUR ACCESS KEY> \
        --environment AWS_SECRET_ACCESS_KEY=<YOUR SECRET> \
        --package-bucket-name <YOUR BUCKET> \
        --package-object-name <OBJECT NAME, eg: dist.zip>

Now you can test your function. For example, you can scan `dist.zip` itself:

    $ yc serverless function invoke clamscan --data '{"messages":[{"details":{"bucket_id":"<YOUR BUCKET>","object_id":"dist.zip"}}]}'
    {"scanned": 1, "infected": 0, "known_viruses": 4564902}
    
Read logs:

    $ yc serverless function logs d4en8ub1ocvfghc6qdtm         
    2020-03-02 21:32:03	START RequestID: 4d00fa6c-8d16-4182-97e0-fa4426d7e435 Version: d4e00000000000000000
    2020-03-02 21:32:06	downloading xxx-dev/dist.zip to /tmp/tmp25o0e8zt
    2020-03-02 21:32:10	downloaded xxx-dev/dist.zip to /tmp/tmp25o0e8zt (size=128248409)
    2020-03-02 21:32:10	scanning /tmp/tmp25o0e8zt
    2020-03-02 21:32:10	LibClamAV Warning: Cannot dlopen libclamunrar_iface: file not found - unrar support unavailable
    2020-03-02 21:32:18	finished scanning /tmp/tmp25o0e8zt
    2020-03-02 21:32:18	END RequestID: 4d00fa6c-8d16-4182-97e0-fa4426d7e435
    2020-03-02 21:32:18	REPORT RequestID: 4d00fa6c-8d16-4182-97e0-fa4426d7e435 Duration: 12670.534 ms Billed Duration: 12700 ms Memory Size: 512 MB Max Memory Used: 9 MB Queuing Duration: 0.026 ms Function Init Duration: 627.553 ms
    
### Connect Object Storage and Function

To connect services we need to create Trigger:

    $ yc serverless trigger create object-storage --name clamav-scanner \
        --bucket-id <YOUR-BUCKET> \
        --events create-object \
        --invoke-function-name clamav-scanner \
        --invoke-function-service-account-name clamav \
        --retry-attempts 3 \
        --retry-interval 10s

Create or update any object in given bucket, and check function logs, it will show that object was checked.

If you need to process every object and want to have guarantees, specify Trigger's Dead Letter Queue (DLQ) options, to
send unprocessed messages to this queue.