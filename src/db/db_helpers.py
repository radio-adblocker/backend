import logging
import os
import threading

from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from src.db import create_and_connect_to_db
import contextvars

logger = logging.getLogger("db_helpers.py")

# create session with the db
Session = sessionmaker(bind=create_and_connect_to_db.engine)

pool_semaphore = threading.Semaphore(int(os.getenv("MAX_CONNECTIONS")))

STATUS = {
    "ad": 1,
    "music": 2,
    "news": 3,
    "nothing": 4,
    "talk": 4  # TODO: maybe add a status for that one
}


def helper_get_allowed_states(connection):
    """
    Helper function to limit returned rows to ones with only allowed states
    @param connection: the connection object mapping the DB table connections
    @return: a list of allowed states
    """

    allowed_states = []
    if connection.preference_music:
        allowed_states.append(STATUS["music"])
    if connection.preference_talk:
        allowed_states.append(STATUS["talk"])
    if connection.preference_news:
        allowed_states.append(STATUS["news"])
    if connection.preference_ad:
        allowed_states.append(STATUS["ad"])
    return allowed_states


current_session = contextvars.ContextVar("current_session", default=None)


class NewTransaction:
    """
    usage:
    with NewTransaction():
       ...
    """

    def __init__(self):
        self.session = None
        self.transaction = None
        self.before = None

    def __enter__(self):
        pool_semaphore.acquire()
        self.session = Session()
        self.transaction = self.session.begin()
        self.transaction.__enter__()
        self.before = current_session.get(None)
        current_session.set(self)
        return self

    def __exit__(self, *args):
        self.transaction.__exit__(*args)
        current_session.set(self.before)
        pool_semaphore.release()

    def first(self, stmt):
        """
        Checks if SQLAlchemy Query result exists, and returns the first result if it does
        @param stmt: The SQLAlchemy Query
        @return: the first result of the SQLAlchemy Query, or None
        """

        result = self.session.execute(stmt).first()
        return None if result is None else (result if len(result) > 1 else result[0])

    def all(self, stmt):
        """
        Prepares the outcome of an SQLAlchemy Query by untupling it
        @param stmt: the SQLAlchemy Query
        @return: the result as list of rows (if with one-tuples, the tuples will be unpacked)
        """

        result = self.session.execute(stmt).all()
        if len(result) == 0:
            return []
        if len(result[0]) > 1:
            return result
        return [entry[0] for entry in result]

    def scalar(self, stmt):
        return self.execute(stmt).scalar()

    def execute(self, stmt, bulk_data=None):
        if bulk_data:
            stmt = stmt.values(bulk_data)
        return self.session.execute(stmt)


def serialize_row(row):
    """
    Helper function to prepare db row in json format
    @param row: the row or rows returned from a SQLAlchemy Query
    @return: The serialized value and key of a row
    """
    if isinstance(row, dict):
        return row
    return {c.key: getattr(row, c.key) for c in inspect(row).mapper.column_attrs}


def serialize_rows(rows):
    """
    Helper function to prepare multiple db rows in json format
    @param rows: the row or rows returned from a SQLAlchemy Query
    @return: The serialized value and key of multiple rows
    """
    return [serialize_row(r) for r in rows]


def serialize(row_or_rows):
    """
    Serializes the input with serializeRow or serializeRows depending on input
    @param row_or_rows: the row or rows returned from a SQLAlchemy Query
    @return: the serialized row
    """
    if isinstance(row_or_rows, list):
        return serialize_rows(row_or_rows)
    elif row_or_rows is None:
        return None
    else:
        return serialize_row(row_or_rows)




