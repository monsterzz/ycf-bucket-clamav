all: clean dependencies package

clean:
	rm -rf dist/

dirs:
	mkdir -p dist/

dependencies: dirs
	docker run --rm \
		-v $(shell pwd)/dist:/dist -v $(shell pwd):/app \
		-w /app \
		monsterzz/clamav-static:latest \
		make docker

docker:
	cp -r /clamav /dist/clamav
	mkdir -p /dist/clamav/cvd
	curl -o /dist/clamav/cvd/main.cvd http://database.clamav.net/main.cvd
	LD_LIBRARY_PATH=/dist/clamav /dist/clamav/clamscan --gen-json=yes --database=/dist/clamav/cvd /dist/clamav/clamscan
	pip3 install -r /app/requirements.txt --target /dist/

install-code: dirs
	cp main.py dist/main.py

package: dirs install-code
	rm -f dist.zip
	cd dist && zip --exclude '*.pyc' -r ../dist.zip ./*

.PHONY: clean dirs dependencies install-code package all
