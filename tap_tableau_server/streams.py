"""Stream type classes for tap-tableau-server."""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, List, Iterable

from singer_sdk.streams import Stream
from singer_sdk import typing as th  # JSON Schema typing helpers


SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class WorkbookIds(Stream):
    """ All workbook id's.
    """
    name = 'workbook_ids'
    primary_keys = ['observed_at']
    schema_filepath = SCHEMAS_DIR / 'workbook_ids.json'

    def get_records(self, partition: Optional[dict]) -> Iterable[Dict[str, Any]]:
        yield {
            'observed_at': datetime.now().isoformat(),
            'workbook_ids': self._tap.client.list_all_workbook_ids()
        }


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
        limit = self.config.get('limit')
        # Get workbooks from server
        for lwb in self._tap.client.get_workbooks(checkpoint=checkpoint, limit=limit):
            record, datasources = self._tap.wbx.extract_workbook(workbook=lwb)
            child_context = {
                'workbook_id': lwb.id,
                'updated_at': lwb.wbi.updated_at.isoformat(),
                'datasources': datasources
            }
            yield (record, child_context)


class WorkbookDatasource(Stream):
    """ Tableau Workbook Datasources
    """

    name = 'workbook_datasource'
    primary_keys = ['id']
    replication_key = 'updated_at'
    schema_filepath = SCHEMAS_DIR / 'workbook_datasource.json'
    # Parent Stream Details
    parent_stream_type = Workbook
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Tuple]:
        for ds in context['datasources']:
            record, connections = self._tap.wbx.extract_datasource(
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
    replication_key = 'updated_at'
    schema_filepath = SCHEMAS_DIR / 'workbook_connection.json'
    # Parent Stream Details
    parent_stream_type = WorkbookDatasource
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Tuple]:
        for conn in context['connections']:
            connections = self._tap.wbx.extract_connection(
                workbook_id=context['workbook_id'],
                datasource_id=context['datasource_id'],
                updated_at=context['updated_at'],
                connection=conn
            )
            # One Connection can contain many 'named connection' records
            for record, relation in connections:
                child_context = {
                    'workbook_id': context['workbook_id'],
                    'datasource_id': context['datasource_id'],
                    'connection_id': record['id'],
                    'updated_at': context['updated_at'],
                    'relation': relation
                }
                yield (record, child_context)


class WorkbookRelation(Stream):
    """ Tableau Workbook Relations
    """

    name = 'workbook_relation'
    primary_keys = ['id']
    replication_key = 'updated_at'
    schema_filepath = SCHEMAS_DIR / 'workbook_relation.json'
    # Parent Stream Details
    parent_stream_type = WorkbookConnection
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Tuple]:
        relations = self._tap.wbx.extract_relation(
            workbook_id=context['workbook_id'],
            datasource_id=context['datasource_id'],
            updated_at=context['updated_at'],
            relation=context['relation']
        )
        # One Relation block can contain many Relations
        if relations:
            for record in relations:
                yield (record, record)


class WorkbookTableReference(Stream):
    """ Tableau Workbook Table References
    """

    name = 'workbook_table_reference'
    primary_keys = ['id']
    replication_key = 'updated_at'
    schema_filepath = SCHEMAS_DIR / 'workbook_table_reference.json'
    # Parent Stream Details
    parent_stream_type = WorkbookRelation
    state_partitioning_keys = []

    def get_records(self, context: Dict) -> Iterable[Dict]:
        table_references = self._tap.wbx.extract_table_references(
            relation=context
        )
        for table_ref in table_references:
            yield table_ref
