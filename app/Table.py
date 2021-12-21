from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy


class Table:

    def __init__(self, database: SQLAlchemy, table_name: str):
        self.database = database
        self.table_name = table_name
        self.field_types = self.get_field_types()


    def select(self, columns: list, condition=None):

        query = text(f"""
        SELECT {', '.join(columns)}
        FROM {self.table_name}
        {f'WHERE {condition}' if condition else None}
        """)
        with self.database.engine.connect() as connection:
            result = [{columns[i]: value for i, value in enumerate(record)} for record in connection.execute(query)]
            return result


    def insert(self, columns: list, values: list):

        values = list(map(lambda v: str(v).replace("'", "''"), values))

        query = text(f"""
        INSERT INTO {self.table_name}
        ({', '.join(columns)})
        VALUES ({', '.join([self.add_qutoes_to_string_field(col, val) for col, val in zip(columns, values)])})
        """)

        with self.database.engine.connect() as connection:
            result = connection.execute(query)
            return result


    def update(self, columns: list, values: list, condition=None):

        values = list(map(lambda v: str(v).replace("'", "''"), values))

        query = text(f"""
        UPDATE {self.table_name}
        SET {', '.join([f"{col}={self.add_qutoes_to_string_field(col, val)}" for col, val in zip(columns, values)])}
        {f"WHERE {condition}" if condition else ""}
        """)

        with self.database.engine.connect() as connection:
            result = connection.execute(query)
            return result


    def delete(self, condition=None):

        query = text(f"""
        DELETE FROM {self.table_name}
        {f"WHERE {condition}" if condition else ""}
        """)

        with self.database.engine.connect() as connection:
            result = connection.execute(query)
            return result


    def describe(self):

        query = text(f"DESCRIBE {self.table_name}")

        with self.database.engine.connect() as connection:
            result = connection.execute(query)
            return result
    
    
    @property
    def field_names(self):
        return ', '.join(map(lambda row: row[0], self.describe()))


    def get_field_types(self):
        field_descriptions = self.describe()
        return {field[0]: str(field[1]) for field in field_descriptions}


    def add_qutoes_to_string_field(self, field_name, value):
        field_type = self.field_types.get(field_name)
        string_types = ['varchar', 'text']
        for string_type in string_types:
            if string_type in field_type.lower():
                return f"'{value}'"
        return value


    def __str__(self):
        return '\n'.join(map(lambda params: ', '.join(params), self.describe()))