from src.config import read_yaml


class Builder:
    def __init__(self, cls):
        self.attributes = []
        self.groups = []
        self.queries = []
        self.cls = cls

        self.conf = read_yaml('config.yaml')
        self.DOMAIN = self.conf['domain']

    def parse(self, cls, attrs: dict):
        for attribute in attrs:
            if attribute in cls.group_by:
                self.groups.append(
                    f'(GROUP_CONCAT(DISTINCT ?{attrs[attribute]}; SEPARATOR=", ") AS ?{attrs[attribute]}s)'
                )
            else:
                self.attributes.append(f'?{attrs[attribute]}')

            query = ['OPTIONAL{'] + [f'?{cls.get_prefix()} {self.DOMAIN}:{attribute} ?{attrs[attribute]}.'] + ['}']
            self.queries.append(''.join(query))

    def where(self, attribute: str, val: str):
        self.queries.append(f'FILTER (?{attribute}="{val}").')
        return self

    def query(self):
        query = ['{'] + [f'?{self.cls.get_prefix()} a {self.DOMAIN}:{self.cls.prefix}'] + ['}']
        self.queries = [''.join(query)]
        self.parse(self.cls, self.cls.get_attributes())

        relations = self.cls.get_objects()
        for relation in relations:
            relation_cls = relations[relation]

            query = ['OPTIONAL{'] + [f'?{self.cls.get_prefix()} {self.DOMAIN}:{relation} ?{relation_cls.get_prefix()}'] + ['}']
            self.queries.append(''.join(query))
            self.parse(relation_cls, relation_cls.get_attributes())

        return self

    def get(self):
        items = self.conf['namespaces']
        items = items + ['SELECT DISTINCT'] + self.attributes + self.groups
        items = items + ['WHERE {'] + self.queries + ['}']

        if len(self.groups):
            items = items + ['GROUP BY'] + self.attributes

        return ' '.join(items)

