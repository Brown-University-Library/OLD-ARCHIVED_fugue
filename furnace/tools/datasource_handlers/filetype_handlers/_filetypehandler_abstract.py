from abc import ABC, abstractmethod


class Abstract_FileHandler(ABC):
    @classmethod
    def default(cls):
        try:
            return bool(cls.Meta.default)
        except:
            return False

    @classmethod
    def mimetypes(cls):
        try:
            return cls.Meta.mimetypes
        except:
            return []

    @abstractmethod
    def process(path):
        """Reads a datasource and adds it to the provided XML element."""
        
        """`path` is a pathlib.Path pointing to a file. Either the file's mimetype
            matches one of the items in self.mimetypes or self.default is True."""

        """Returns an ETree XMLElement"""
        pass