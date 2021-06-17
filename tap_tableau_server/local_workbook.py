import os
import json
import errno
from datetime import date, datetime

import tableauserverclient as TSC
from tableaudocumentapi import Workbook, Datasource

from .utils import json_serial


WORKBOOKITEM_EXTRACT_ATTRS = [
    'id', 'created_at', 'updated_at', 'name',
    'project_id', 'project_name', 'size', 'tags',
    'content_url', 'webpage_url', 'owner_id'
]
WORKBOOK_FILE_EXTRACT_ATTRS = ['filename']


class LocalWorkbook:
    """ Container class for tableauserverclient.WorkbookItem
    and tableaudocumentapi.Workbook objects.
    """

    def __init__(self, workbook_item, workbook=None):
        self.wbi = workbook_item
        self.wb = workbook

    def __getattr__(self, name):
        try:
            return getattr(self.wbi, name)
        except AttributeError:
            pass
        try:
            return getattr(self.wb, name)
        except AttributeError:
            pass
        raise AttributeError

    @classmethod
    def _generate_filepath(cls, workbook_id, base_folder=None):
        if not base_folder:
            base_folder = os.getcwd()
        return os.path.join(base_folder, f"{workbook_id}/")

    @staticmethod
    def _make_dir(path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    @classmethod
    def from_tableau_server(
        cls, server, workbook_id, base_folder=None,
        download_workbook=False, download_with_extract=False,
        keep_backup=False
    ):
        """ Create a LocalWorkbook by fetching a WorkbookItem and downloading
        a Workbook from Tableau Server.
        """
        workbook_item = server.workbooks.get_by_id(workbook_id)
        if workbook_item:
            workbook = None
            workbook_filepath = None
            if download_workbook:
                base_filepath = cls._generate_filepath(workbook_item.id, base_folder)
                cls._make_dir(base_filepath)
                workbook_filepath = server.workbooks.download(
                    workbook_id=workbook_id, filepath=base_filepath, no_extract=(~download_with_extract)
                )
                try:
                    workbook = Workbook(workbook_filepath)
                except AttributeError:
                    pass
                if (workbook is not None) and keep_backup:
                    workbook.save_as(workbook.filename + '.backup')
            return cls(workbook_item=workbook_item, workbook=workbook)

    @classmethod
    def from_local_workbook_dir(cls, server, lwb_dir):
        workbook_item_id = os.path.basename(lwb_dir)
        # Discover Workbook File
        files = []
        for file in os.listdir(lwb_dir):
            if file.endswith(('.twb', '.twbx')):
                files.append(os.path.join(lwb_dir, file))
        if len(files) == 1:
            workbook_filepath = files[0]
        elif len(files) == 0:
            raise ValueError(f'No .twb or .twbx files found in local workbook dir {lwb_dir}')
        else:
            raise ValueError(f'Multiple .twb or .twbx files found in local workbook dir {lwb_dir}')
        # Fetch WorkbookItem
        workbook_item = server.workbooks.get_by_id(workbook_item_id)
        if workbook_item:
            workbook = Workbook(workbook_filepath)
        # Instantiate LocalWorkbook
        return cls(workbook_item=workbook_item, workbook=workbook)

    def to_dict(self):
        wb = {}
        # Populate WorkbookItem attrs
        wbi_attrs = WORKBOOKITEM_EXTRACT_ATTRS
        wbi = {k:getattr(self.wbi, k) for k in wbi_attrs}
        wb['workbook_item'] = wbi
        # Populate Workbook (file) attrs
        if self.wb:
            wbf_attrs = WORKBOOK_FILE_EXTRACT_ATTRS
            wbf = {k:getattr(self.wb, k) for k in wbf_attrs}
            wb['workbook'] = wbf
        return wb

    def to_json(self, **kwargs):
        default_kwargs = {
            'indent': 2,
            'sort_keys': True,
            'default': json_serial
        }
        default_kwargs.update(kwargs)
        return json.dumps(
            self.to_dict(),
            **default_kwargs
        )

    def has_custom_sql(self):
        any_has_custom_sql = []
        for ds in self.wb.datasources:
            if ds.table_relations is not None:
                if ds.table_relations.custom_sql is not None:
                    any_has_custom_sql.append(True)
                    continue
            any_has_custom_sql.append(False)
        return any(any_has_custom_sql)

    def custom_sql_apply(self, func, *args, **kwargs):
        custom_sql = []
        for ds in self.wb.datasources:
            tbr = ds.table_relations
            if tbr is not None:
                if tbr.type == 'text':
                    tbr.custom_sql = func(tbr.custom_sql, *args, **kwargs)
                    custom_sql.append(tbr.custom_sql)
        return custom_sql

    def publish(self, server, auth, publish_mode='Overwrite'):
        self.wb.save()
        with server.auth.sign_in(auth):
            self.wbi = server.workbooks.publish(
                workbook_item=self.wbi, file_path=self.wb.filename,
                mode=publish_mode
            )

    def delete_file(self):
        if self.wb:
            try:
                os.remove(self.wb.filename)
            except OSError:
                pass
