import sqlite3
from contextlib import closing


def dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def connect(dbpath):
    con = sqlite3.connect(dbpath)
    con.row_factory = dict_factory
    return con


def enable_wal(db):
    with closing(db.cursor()) as cur:
        cur.execute("PRAGMA journal_mode=WAL;")
        db.commit()
