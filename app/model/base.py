class BaseModel:

    def row_normalize(self, row):
        if not row:
            return row

        if isinstance(row, list):
            normalized = []
            for r in row:
                d = {}
                for p in r.primary_key:
                    d[p[0]] = p[1]
                for c in r.attribute_columns:
                    d[c[0]] = c[1]
                normalized.append(d)
        else:
            normalized = {}
            for p in row.primary_key:
                normalized[p[0]] = p[1]
            for c in row.attribute_columns:
                normalized[c[0]] = c[1]

        return normalized

    def page_normalize(self, row):
        if not row:
            return row

        normalized = []
        for r in row:
            d = {}
            for pk in r[0]:
                d[pk[0]] = pk[1]
            for attr in r[1]:
                d[attr[0]] = attr[1]
            normalized.append(d)

        return normalized
