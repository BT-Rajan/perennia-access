"""Database connection management."""

from contextlib import contextmanager

import pymysql
import pymysql.cursors

from .config import DatabaseConfig
from .exceptions import AccessDatabaseError


class Database:
    """Thin connection/transaction wrapper. Not a multi-engine abstraction."""

    def __init__(self, config: DatabaseConfig):
        self._config = config

    def _connect(self):
        try:
            return pymysql.connect(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                charset=self._config.charset,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        except pymysql.MySQLError as e:
            raise AccessDatabaseError(f"Database connection failed: {str(e)}") from e

    @contextmanager
    def transaction(self):
        """Yields a cursor. Commits on success, rolls back on any exception."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            yield cur
            conn.commit()
        except pymysql.MySQLError as e:
            conn.rollback()
            raise AccessDatabaseError(f"Query execution failed: {str(e)}") from e
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def cursor(self):
        """Read-only convenience cursor."""
        conn = self._connect()
        try:
            cur = conn.cursor()
            yield cur
        except pymysql.MySQLError as e:
            raise AccessDatabaseError(f"Query execution failed: {str(e)}") from e
        finally:
            conn.close()

    def execute(self, query: str, args: tuple = None) -> list:
        """Execute a SELECT query and return results. Opens/closes its own connection."""
        with self.cursor() as cur:
            cur.execute(query, args or ())
            return cur.fetchall()

    def execute_insert(self, query: str, args: tuple = None) -> int:
        """Execute an INSERT query and return the inserted ID. Commits or rolls back."""
        with self.transaction() as cur:
            cur.execute(query, args or ())
            return cur.lastrowid

    def execute_delete(self, query: str, args: tuple = None) -> int:
        """Execute a DELETE query and return the number of affected rows."""
        with self.transaction() as cur:
            cur.execute(query, args or ())
            return cur.rowcount
