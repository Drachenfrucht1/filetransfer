# file transfer


## How to use it
- Drop a file into the drop zone or select one by opening the file browser.
- The file gets uploaded to the server and you get redirected the download site.
- Share the url or qrcode so others can download the file.
- The file will be deleted after 10 minutes.

## Setup
- Install all required software using ```pip install -r requirements.txt```.
- Rename example_config.py to config.py.
- Update the ```redis_host``` and ```redis_port``` variables to point to a redis instance.
- Select one of the following storage drivers and configure it.
- Start the server using ```python start.py```.

#### Filesytem Storage Driver
- Set ```storage_driver``` in the config file to ```storage.FileSystemStorageDriver```.
- Set a file location using the ```file_location``` option.
- The uploaded files will be stored in the ```file_location``` on the server.

#### S3 Storage Driver
- Set ```storage_driver``` in the config file to ```storage.S3StorageDriver```.
- Point the ```S3_ACCESS_KEY,S3_SECREET_KEY,S3_REGION,S3_ENDPOINT``` and ```S3_BUCKET``` options to a S3
instance.
- The uploaded files will be stored in the s3 bucket.

#### S3 Storage Driver Extern
- Set ```storage_driver``` in the config file to ```storage.S3StorageDriverExtern```.
- Point the ```S3_ACCESS_KEY,S3_SECREET_KEY,S3_REGION,S3_ENDPOINT``` and ```S3_BUCKET``` options to a S3 instance.
- The uploaded files will be stored in the s3 bucket. They will be directly up loaded to the s3 bucket from the webbrowser using presigned urls. The download is directly from the s3 bucket as well using presigned urls.

## Used software
- [pico.css](https://picocss.com/)
- [qrcode](https://github.com/davidshimjs/qrcodejs)
- [Font Awesome](https://fontawesome.com)
- [bottle](https://bottlepy.org)
