import  abc
from inspect import signature
import os

from config import config

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
    def delete(self, id):
        pass

    @abc.abstractmethod
    def get(self, id):
        pass

class FileSystemStorageDriver(StorageDriver):
    def store(self, id, file):
        # see FileUpload._copy_file
        chunksize = 2 ** 16
        with open(os.path.join(config['file_location'], id), 'wb') as f:
            while True:
                buf = file.read()
                if not buf: break
                f.write(buf)

    def delete(self, id):
         os.remove(os.path.join(config['file_location'], id))

    def get(self, id):
        return open(os.path.join(config['file_location'], id), 'rb')