"""Database connection management."""

import pymysql
from pymysql.cursors import DictCursor
from .config import DatabaseConfig
from .exceptions import AccessDatabaseError


class Database:
    """Manages MySQL connections for perennia-access."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
    
    def connect(self):
        """Establish a connection to the database."""
        try:
            self._connection = pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset=self.config.charset,
                cursorclass=DictCursor,
            )
        except pymysql.MySQLError as e:
            raise AccessDatabaseError(f"Database connection failed: {str(e)}") from e
    
    def disconnect(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, args: tuple = None) -> list:
        """Execute a SELECT query and return results."""
        if not self._connection:
            raise AccessDatabaseError("Database connection not established")
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, args or ())
                return cursor.fetchall()
        except pymysql.MySQLError as e:
            raise AccessDatabaseError(f"Query execution failed: {str(e)}") from e
    
    def execute_insert(self, query: str, args: tuple = None) -> int:
        """Execute an INSERT query and return the inserted ID."""
        if not self._connection:
            raise AccessDatabaseError("Database connection not established")
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, args or ())
                self._connection.commit()
                return cursor.lastrowid
        except pymysql.MySQLError as e:
            self._connection.rollback()
            raise AccessDatabaseError(f"Insert failed: {str(e)}") from e
    
    def execute_delete(self, query: str, args: tuple = None) -> int:
        """Execute a DELETE query and return the number of affected rows."""
        if not self._connection:
            raise AccessDatabaseError("Database connection not established")
        
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, args or ())
                self._connection.commit()
                return cursor.rowcount
        except pymysql.MySQLError as e:
            self._connection.rollback()
            raise AccessDatabaseError(f"Delete failed: {str(e)}") from e
