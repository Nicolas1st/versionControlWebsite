from sqlalchemy import text


def select(database, table, columns=[], condition=None):
    query = text(f"""
        SELECT {', '.join(columns)}
        FROM {table}
        {f'WHERE {condition}' if condition else None}
        """)
    with database.engine.connect() as connection:
        result = [{columns[i]: value for i, value in enumerate(record)} for record in connection.execute(query)]
        return result


def insert(database, table, columns=[], values=[]):
    query = text(f"""
        INSERT INTO {table}
        ({', '.join(columns)})
        VALUES ({', '.join(map(lambda s: f"'{s}'", values))})
        """)
    with database.engine.connect() as connection:
        res = connection.execute(query)
        return res


def update(database, table, columns=[], values=[], condition=None):
    query = text(f"""
        UPDATE {table}
        SET {', '.join(map(lambda dr: f"{dr[0]}='{dr[1]}'", zip(columns, values)))}
        {f'WHERE {condition}' if condition else None}
        """)
    with database.engine.connect() as connection:
        res = connection.execute(query)
        return res