"""Stream type classes for tap-tableau-server."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, List, Iterable

from singer_sdk.streams import Stream
from singer_sdk import typing as th  # JSON Schema typing helpers


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class Workbook(Stream):
    """ Tableau Workbooks
    """
    name = 'workbook'
    primary_keys = ['id']
    replication_key = 'updated_at'
    schema_filepath = SCHEMAS_DIR / 'workbook.json'

    def get_records(self, context) -> Iterable[Tuple]:
        # Get checkpoint
        checkpoint = self.stream_state.get('replication_key_value')
        # Get workbooks from server
        for lwb in self.tap.client.get_workbooks(checkpoint=checkpoint):
            record, datasources = self.tap.wbx.extract_workbook(workbook=lwb)
            child_context = {
                'workbook_id': lwb.id,
                'updated_at': lwb.wbi.updated_at,
                'datasources': datasources
            }
            yield (record, child_context)


class WorkbookDatasource(Stream):
    """ Tableau Workbook Datasources
    """

    name = 'workbook_datasource'
    primary_keys = ['id']
    schema_filepath = SCHEMAS_DIR / 'workbook_datasource.json'
    # Parent Stream Details
    parent_stream_type = Workbook
    ignore_parent_replication_key = True
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Tuple]:
        for ds in context['datasources']:
            record, connections = self.tap.wbx.extract_datasource(
                workbook_id=context['workbook_id'],
                updated_at=context['updated_at'],
                datasource=ds
            )
            child_context = {
                'workbook_id': context['workbook_id'],
                'datasource_id': record['id'],
                'updated_at': context['updated_at'],
                'connections': connections
            }
            yield (record, child_context)


class WorkbookConnection(Stream):
    """ Tableau Workbook Connections
    """

    name = 'workbook_connection'
    primary_keys = ['id']
    schema_filepath = SCHEMAS_DIR / 'workbook_connection.json'
    # Parent Stream Details
    parent_stream_type = WorkbookDatasource
    ignore_parent_replication_key = True
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Dict]:
        for conn in context['connections']:
            records, _ = self.tap.wbx.extract_connection(
                workbook_id=context['workbook_id'],
                datasource_id=context['datasource_id'],
                updated_at=context['updated_at'],
                connection=conn
            )
            # One Connection can contain many 'named connection' records
            for record in records:
                yield record


# class WorkbookIds(Stream):
#     """ All workbook id's.
#     """
#     name = 'workbook_ids'
#     primary_keys = ['observed_at']
#     schema_filepath = SCHEMAS_DIR / 'workbook_ids.json'

#     def get_records(self, partition: Optional[dict]) -> Iterable[Dict[str, Any]]:
#         yield {
#             'observed_at': self.tableau_service.observed_at,
#             'workbook_ids': self.tableau_service.remote_workbook_ids
#         }


# class WorkbookRelation(TableauWorkbookFile):
#     """ Tableau Workbook Relations
#     """

#     name = 'workbook_relation'
#     primary_keys = ['id']
#     replication_key = 'updated_at'
#     schema_filepath = SCHEMAS_DIR / 'workbook_relation.json'
#     service_attr = 'workbook_relations'


# class WorkbookTableReference(TableauWorkbookFile):
#     """ Tableau Workbook Table References
#     """

#     name = 'workbook_table_reference'
#     primary_keys = ['id']
#     replication_key = 'updated_at'
#     schema_filepath = SCHEMAS_DIR / 'workbook_table_reference.json'
#     service_attr = 'workbook_table_references'
