from app.model.base import BaseModel
from app.core.table_store import TableStore


class SyncFileModel(BaseModel):

    def __init__(self):
        self.table_sync_files = TableStore('sync_files')
        # 索引 md5(str)
        self.index_name = 'hash_index'

    def get_version_by_hash(self, hash):
        rows, _ = self.table_sync_files.pagination(
            index_name=self.index_name,
            equal={'md5': [hash, ]},
            limit=1,
        )
        if rows:
            row = rows[0]
            result = self.page_normalize(row)
            return result.get('version', '')
        return ''
