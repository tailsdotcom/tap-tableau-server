"""TableauServer tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_tableau_server.client import TableauServerClient
from tap_tableau_server.local_workbook_extractor import LocalWorkbookExtractor
from tap_tableau_server.streams import (
    Workbook, WorkbookDatasource, WorkbookConnection
)


STREAM_TYPES = [
    Workbook, WorkbookDatasource, WorkbookConnection
]


class TapTableauServer(Tap):
    """TableauServer tap class."""

    name = "tap-tableau-server"
    config_jsonschema = th.PropertiesList(
        th.Property("host", th.StringType, required=True),
        th.Property("username", th.StringType, required=True),
        th.Property("password", th.StringType, required=True),
        th.Property("batch_size", th.IntegerType, default=50)
    ).to_dict()
    # Private Attrs
    _tableau_server_client = None
    _wbx = None

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]

    @property
    def client(self):
        """ Tableau Server Client
        """
        if self._tableau_server_client is None:
            self._tableau_server_client = TableauServerClient(
                host=self.config['host'],
                username=self.config['username'],
                password=self.config['password']
            )
        return self._tableau_server_client

    @property
    def wbx(self):
        """ Workbook Extractor
        """
        if self._wbx is None:
            self._wbx = LocalWorkbookExtractor(
                relation_types_exclude=self.config.get('relation_types_exclude'),
                relation_types_include=self.config.get('relation_types_include')
            )
        return self._wbx
