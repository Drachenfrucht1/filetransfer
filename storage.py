import  abc
from inspect import signature
from io import BytesIO
import json
import os
import boto3
from typing import IO, Any

class StorageDriver(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'store') and
            callable(subclass.store) and
            len(signature(subclass.store).parameters) == 3 and
            hasattr(subclass, 'delete') and
            callable(subclass.delete) and
            len(signature(subclass.store).parameters) == 2 and
            hasattr(subclass, 'get') and
            callable(subclass.get) and
            len(signature(subclass.store).parameters) == 2 or
            NotImplemented)

    @abc.abstractmethod
    def store(self, id, file):
        pass

    @abc.abstractmethod
    def delete(self, id) -> None:
        pass

    @abc.abstractmethod
    def get(self, id) -> (str | IO):
        pass

    @abc.abstractmethod
    def required_config(self) -> dict[str, Any]:
        pass

    @property
    def extern(self) -> bool:
        return False

class FileSystemStorageDriver(StorageDriver):

    def __init__(self, config) -> None:
        self.config = config

    def store(self, id, file) -> (None | str):
        # see FileUpload._copy_file
        chunksize = 2 ** 16
        with open(os.path.join(self.config['file_location'], id), 'wb') as f:
            while True:
                buf = file.read()
                if not buf: break
                f.write(buf)

    def delete(self, id) -> None:
         os.remove(os.path.join(self.config['file_location'], id))

    def get(self, id) -> (str | IO):
        return open(os.path.join(self.config['file_location'], id), 'rb')

    def required_config(self) -> list[str]:
        return {'file_location': 'files'}

class S3StorageDriverExtern(StorageDriver):

    def __init__(self, config):
        self.config = config
        try:
            session = boto3.session.Session()
            self._s3_client = session.client('s3', 
                                             region_name=config['S3_REGION'],
                                             endpoint_url=config['S3_ENDPOINT'],
                                             aws_access_key_id=config['S3_ACCESS_ID'], 
                                             aws_secret_access_key=config['S3_SECRET_KEY'])
        except Exception as e:
            raise Exception("""Could not connect to s3 instance. 
                          Make sure S3_ACCESS_ID, S3_SECRET_KEY and S3_BUCKET are correctly defined in the config.""")
        
        response = self._s3_client.list_buckets()
        for bucket in response['Buckets']:
            if bucket['Name'] == config['S3_BUCKET']:
                return

        raise Exception('Could not find bucket ' + config['S3_BUCKET'] + '.')

    def store(self, id, file) -> (None | str):
        response = self._s3_client.generate_presigned_post(self.config['S3_BUCKET'], id, ExpiresIn=60)
        for k in response['fields'].keys():
            response[k] = response['fields'][k]
        del response['fields']
        return json.dumps(response)

    def delete(self, id) -> None:
        self._s3_client.delete_object(Bucket=self.config['S3_BUCKET'], Key=id)

    def get(self, id) -> (str | IO):
        params = {'Bucket': self.config['S3_BUCKET'],
                  'Key': id}
        return self._s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=60)

    def required_config(self) -> dict[str, Any]:
        return {'S3_ACCESS_KEY': '',
                'S3_SECRET_KEY': '',
                'S3_REGION': '',
                'S3_ENDPOINT': '',
                'S3_BUCKET': 'file_transfer'}

    @property
    def extern(self) -> bool:
        return True

class S3StorageDriver(StorageDriver):

    def __init__(self, config):
        self.config = config
        try:
            session = boto3.session.Session()
            self._s3_client = session.client('s3', 
                                             region_name=config['S3_REGION'],
                                             endpoint_url=config['S3_ENDPOINT'],
                                             aws_access_key_id=config['S3_ACCESS_ID'], 
                                             aws_secret_access_key=config['S3_SECRET_KEY'])
        except Exception as e:
            raise Exception("""Could not connect to s3 instance. 
                          Make sure S3_ACCESS_ID, S3_SECRET_KEY and S3_BUCKET are correctly defined in the config.""")
        
        response = self._s3_client.list_buckets()
        for bucket in response['Buckets']:
            if bucket['Name'] == config['S3_BUCKET']:
                return

        raise Exception('Could not find bucket ' + config['S3_BUCKET'] + '.')

    def store(self, id, file) -> (None | str):
        self._s3_client.upload_fileobj(file, self.config['S3_BUCKET'], id)

    def delete(self, id) -> None:
        self._s3_client.delete_object(Bucket=self.config['S3_BUCKET'], Key=id)

    def get(self, id) -> (str | IO):
        file_obj = BytesIO()
        a = self._s3_client.get_object(Bucket=self.config['S3_BUCKET'], Key=id)['Body'].read()
        return a


    def required_config(self) -> dict[str, Any]:
        return {'S3_ACCESS_KEY': '',
                'S3_SECRET_KEY': '',
                'S3_REGION': '',
                'S3_ENDPOINT': '',
                'S3_BUCKET': 'file_transfer'}

    @property
    def extern(self) -> bool:
        return False