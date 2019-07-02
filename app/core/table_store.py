from config import Config
from tablestore import (
    OTSClient, OTSClientError, OTSServiceError,
    Row, Condition, RowExistenceExpectation,
    SingleColumnCondition, ComparatorType, CompositeColumnCondition, LogicalOperator,
    Direction, INF_MIN, INF_MAX,
    Sort, FieldSort, SortOrder, SearchQuery, MatchAllQuery, BoolQuery, TermsQuery,
    ColumnsToGet, ColumnReturnType,
    BatchWriteRowRequest,
)
from app.core.errors import TableStoreServiceError


class TableStore:
    """
    https://www.alibabacloud.com/help/zh/doc-detail/31723.htm
    """
    def __init__(self, table_name):
        self._client = OTSClient(
            access_key_id=Config['aliyun']['access_key'],
            access_key_secret=Config['aliyun']['access_secret'],
            end_point=Config['tablestore']['ots_endpoint'],
            instance_name=Config['tablestore']['ots_instance'],
        )
        self._table_name = table_name

    def add_row(self, primary_key, attribute_columns):
        row = Row(primary_key=primary_key, attribute_columns=attribute_columns)
        condition = Condition(RowExistenceExpectation.EXPECT_NOT_EXIST)
        consumed, return_row = self._client.put_row(self._table_name, row, condition)
        return return_row

    def get_row(self, primary_key, **kwargs):
        condition = None
        if kwargs:
            k, v = kwargs.popitem()
            condition = SingleColumnCondition(
                k, v, ComparatorType.EQUAL, pass_if_missing=False
            )
        consumed, row, next_token = self._client.get_row(
            table_name=self._table_name,
            primary_key=primary_key,
            column_filter=condition,
        )
        return row

    def pagination(self, index_name, offset=0, limit=10,
                   sort_fields_and_order=None,
                   equal=None, not_equal=None):

        must_queries = [MatchAllQuery(), ]
        must_not_queries = []
        # https://help.aliyun.com/document_detail/106362.html
        if equal:
            for k, v in equal.items():
                must_queries.append(TermsQuery(k, v))
        if not_equal:
            for k, v in not_equal.items():
                must_not_queries.append(TermsQuery(k, v))

        query = BoolQuery(must_queries=must_queries, must_not_queries=must_not_queries)
        sorters = []
        if sort_fields_and_order:
            for s in sort_fields_and_order:
                so = SortOrder.ASC if s[1].upper() == 'ASC' else SortOrder.DESC
                st = FieldSort(s[0], so)
                sorters.append(st)

        search_query = SearchQuery(
            query=query,
            sort=Sort(sorters=sorters),
            offset=offset,
            limit=limit,
            get_total_count=True,
        )
        try:
            rows, next_token, total_count, is_all_succeed = self._client.search(
                table_name=self._table_name,
                index_name=index_name,
                search_query=search_query,
                columns_to_get=ColumnsToGet(return_type=ColumnReturnType.ALL),
            )
        except OTSServiceError as e:
            raise TableStoreServiceError(msg=e.message)
        # Todo if not is_all_succeed

        return rows, total_count

    def get_first_row(self, primary_key_names, **kwargs):
        result = self.get_rows(
            primary_key_names=primary_key_names,
            direction='asc', limit=1, **kwargs
        )
        return result[0] if result else None

    def get_last_row(self, primary_key_names, **kwargs):
        result = self.get_rows(
            primary_key_names=primary_key_names,
            direction='desc', limit=1, **kwargs
        )
        return result[0] if result else None

    def get_rows(self, primary_key_names=None, inclusive_start=None, exclusive_end=None,
                 direction='asc', columns_to_get=None, limit=None, **kwargs):
        if not (primary_key_names or inclusive_start or exclusive_end):
            raise OTSClientError('primary_key_names or start/end must be set')

        if direction == 'asc':
            min, max, direction = INF_MIN, INF_MAX, Direction.FORWARD
        else:
            min, max, direction = INF_MAX, INF_MIN, Direction.BACKWARD

        if primary_key_names:
            if isinstance(primary_key_names, list):
                inclusive_start = []
                exclusive_end = []
                for i in range(0, len(primary_key_names)):
                    inclusive_start.append((primary_key_names[i], min))
                    exclusive_end.append((primary_key_names[i], max))
            elif isinstance(primary_key_names, str):
                inclusive_start = [(primary_key_names, min)]
                exclusive_end = [(primary_key_names, max)]
            else:
                raise OTSClientError('primary_key_names type must be list or str')
        elif inclusive_start is None:
            inclusive_start = []
            for i in range(0, len(exclusive_end)):
                inclusive_start.append((exclusive_end[i][0], min))
        elif exclusive_end is None:
            exclusive_end = []
            for i in range(0, len(inclusive_start)):
                exclusive_end.append((inclusive_start[i][0], max))

        condition = None
        all_rows = []
        if kwargs:
            if len(kwargs) == 1:
                k, v = kwargs.popitem()
                condition = SingleColumnCondition(
                    k, v, ComparatorType.EQUAL, pass_if_missing=False
                )
            else:
                condition = CompositeColumnCondition(LogicalOperator.AND)
                for k, v in kwargs.items():
                    condition.add_sub_condition(SingleColumnCondition(
                        k, v, ComparatorType.EQUAL, pass_if_missing=False
                    ))

        try:
            consumed, next_start_primary_key, row_list, next_token = self._client.get_range(
                table_name=self._table_name,
                column_filter=condition,
                direction=direction,
                inclusive_start_primary_key=inclusive_start,
                exclusive_end_primary_key=exclusive_end,
                columns_to_get=columns_to_get,
                limit=limit,
                max_version=1,
            )
        except OTSServiceError as e:
            raise TableStoreServiceError(msg=e.message)

        all_rows.extend(row_list)

        if limit:
            return all_rows

        while next_start_primary_key is not None:
            start_primary_key = next_start_primary_key
            consumed, next_start_primary_key, row_list, next_token = self._client.get_range(
                table_name=self._table_name,
                column_filter=condition,
                direction=direction,
                inclusive_start_primary_key=start_primary_key,
                exclusive_end_primary_key=exclusive_end,
                columns_to_get=columns_to_get,
                limit=limit,
                max_version=1,
            )
            all_rows.extend(row_list)

        return all_rows

    def update_row(self, primary_key, attribute_columns, expect=''):
        expect = expect.upper()

        expectation = RowExistenceExpectation.IGNORE
        if expect == 'NOT_EXIST':
            expectation = RowExistenceExpectation.EXPECT_NOT_EXIST
        if expect == 'EXIST':
            expectation = RowExistenceExpectation.EXPECT_EXIST

        row = Row(primary_key, attribute_columns)
        condition = Condition(expectation)
        consumed, return_row = self._client.update_row(self._table_name, row, condition)
        return return_row

    def batch_update_row(self, primary_key, attribute_columns):
        pass

    def delete_row(self, primary_key):
        row = Row(primary_key=primary_key)
        try:
            consumed, return_row = self._client.delete_row(self._table_name, row, condition=None)
        except OTSClientError as e:
            msg = "Delete row failed, http_status:%d, error_message:%s" % \
                  (e.get_http_status(), e.get_error_message())
            raise TableStoreServiceError(msg)
        except OTSServiceError as e:
            msg = "Delete row failed, http_status:%d, error_code:%s, error_message:%s, request_id: %s" % \
                  (e.get_http_status(), e.get_error_code(), e.get_error_message(), e.get_request_id())
            raise TableStoreServiceError(msg)

        return True
