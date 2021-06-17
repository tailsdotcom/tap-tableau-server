import abc
import pytz
import logging
import tempfile
from datetime import datetime
from dateutil.parser import parse
from typing import Union, List, Iterable

import tableauserverclient as tsc
from tableauserverclient.server.endpoint.exceptions import (
    ServerResponseError, InternalServerError
)

from .utils import retry
from .local_workbook import LocalWorkbook


logger = logging.getLogger('tableau_wrangler.client')
tsc_exceptions = (ServerResponseError, InternalServerError)


class BaseTableauServerClient(metaclass=abc.ABCMeta):
    """ Abstract base class for clients.
    """

    def list_all_workbook_ids(self):
        raise NotImplementedError()


class TableauServerClient(BaseTableauServerClient):
    """ A wrapper around the `tableauserverclient` library.
    """

    def __init__(self, host, username, password):
        self._host = host
        self._username = username
        self._password = password

    @property
    def authentication(self):
        return tsc.TableauAuth(self._username, self._password)

    @property
    def server(self):
        server = tsc.Server(self._host)
        server.version = '3.2'
        return server

    def format_checkpoint_datetime(self, dt):
        return (
            dt.astimezone(pytz.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace('+00:00', 'Z')
        )

    def list_all_workbook_ids(self):
        # Get all WorkbookItem id's, sorted by UpdatedAt
        req_option = tsc.RequestOptions()
        req_option.sort.add(
            tsc.Sort(
                tsc.RequestOptions.Field.UpdatedAt,
                tsc.RequestOptions.Direction.Asc
            )
        )
        workbook_ids = []
        server = self.server
        with server.auth.sign_in(self.authentication):
            workbook_ids = [
                wb.id for wb in tsc.Pager(server.workbooks, req_option)
            ]
        return workbook_ids

    def list_workbook_ids(
        self, checkpoint:Union[datetime, str] = None,
        limit: int = None
    ) -> List[str]:
        # Create client filter object
        req_option = tsc.RequestOptions()
        req_option.sort.add(
            tsc.Sort(
                tsc.RequestOptions.Field.UpdatedAt,
                tsc.RequestOptions.Direction.Asc
            )
        )
        if checkpoint:
            # Format datetime for filter
            if isinstance(checkpoint, datetime):
                cp = self.format_checkpoint_datetime(checkpoint)
            else:
                cp = self.format_checkpoint_datetime(parse(checkpoint))

            req_option.filter.add(
                tsc.Filter(
                    tsc.RequestOptions.Field.UpdatedAt,
                    tsc.RequestOptions.Operator.GreaterThanOrEqual,
                    cp
                )
            )
            # Get filtered id's
            server = self.server
            with server.auth.sign_in(self.authentication):
                workbook_ids = [
                    wb.id for wb in tsc.Pager(server.workbooks, req_option)
                ]
        else:
            # Get all workbook id's
            workbook_ids = self.list_all_workbook_ids()

        # Return, with optional applied limit
        if limit:
            return workbook_ids[:limit]
        else:
            return workbook_ids

    @retry(exceptions=tsc_exceptions, logger=logger, finally_raise=False)
    def get_local_workbook(self, wb_id, base_folder):
        server = self.server
        with server.auth.sign_in(self.authentication):
            return LocalWorkbook.from_tableau_server(
                server=server, workbook_id=wb_id,
                base_folder=base_folder,
                download_workbook=True
            )

    def iterate_server_workbooks(
        self, workbook_ids: List[str]
    ) -> Iterable[LocalWorkbook]:
        for wb_id in workbook_ids:
            try:
                lwb = self.get_local_workbook(wb_id, tempfile.gettempdir())
                if lwb is not None:
                    if lwb.wb is not None:
                        yield lwb
                        lwb.delete_file()
            except GeneratorExit:
                logger.warn("Generator exited early. Not all Workbooks were fetched.")
                lwb.delete_file()
                return
