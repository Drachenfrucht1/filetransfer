import abc
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
    def __init__(self, config) -> None:
        """
        Initializes the storage driver object. The passed config parameter is guaranteed to contain all required config options.

        :param config: configuration dictionary
        :returns: None
        """
        pass


    @abc.abstractmethod
    def store(self, id, file) -> (None | str):
        """
        if not external storage driver: Takes the file object and stores it. The file must be retrievable using the id.
        if external storage driver: Returns a json string containing a dictionary. The file will be uploaded to the url member of the dictionary.
        The file name will be set to the 'file-name' value of the dictionary. All other members of the dictionary will be send as POST options for the request.

        :param id: id of the file
        :param file: none if external storage driver, file to upload otherwise
        :return: None if not external storage driver, json string otherwise
        """
        pass

    @abc.abstractmethod
    def delete(self, id) -> None:
        """
        Deletes the file with the given id

        :param id: id of the file to be deleted
        :returns: None
        """
        pass

    @abc.abstractmethod
    def get(self, id) -> (str | IO):
        """
        if not external storage driver: Returns a IO object that contains the file with the given id
        if external storage driver: returns url string where the file can be downloaded

        :param id: id of the file to be retrieved
        :returns: IO object to file if not external storage driver, string with download url otherwise
        """
        pass

    @staticmethod
    @abc.abstractmethod
    def required_config() -> dict[str, Any]:
        """
        Defines the required config for this. Member names of the returned dictionary are the config parameter names. Values of the dictionary are set as default values.
        
        :returns: dictionary with the required config parameters and their default values.
        """
        pass

    @property
    def extern(self) -> bool:
        """
        Determines if the storage driver is external or not. External storage drivers only returns urls for the upload and download of the file.
        The user's webbrowser will then upload the files directly to the storage backend (e.g. using signed urls for S3). Non-external storage drivers handle the file objects directly.
        """
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

    @staticmethod
    def required_config() -> dict[str, Any]:
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
        response['file-name'] = response['key']
        return json.dumps(response)

    def delete(self, id) -> None:
        self._s3_client.delete_object(Bucket=self.config['S3_BUCKET'], Key=id)

    def get(self, id) -> (str | IO):
        params = {'Bucket': self.config['S3_BUCKET'],
                  'Key': id}
        return self._s3_client.generate_presigned_url('get_object', Params=params, ExpiresIn=60)

    @staticmethod
    def required_config() -> dict[str, Any]:
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

    @staticmethod
    def required_config() -> dict[str, Any]:
        return {'S3_ACCESS_KEY': '',
                'S3_SECRET_KEY': '',
                'S3_REGION': '',
                'S3_ENDPOINT': '',
                'S3_BUCKET': 'file_transfer'}

    @property
    def extern(self) -> bool:
        return False