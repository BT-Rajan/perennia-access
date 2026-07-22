"""Configuration for perennia-access."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """MySQL database configuration."""
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    charset: str = "utf8mb4"


@dataclass
class AccessConfig:
    """perennia-access configuration."""
    database: DatabaseConfig
    
    # Fail-safe mode: if authorization cannot be evaluated,
    # should we deny or allow? Always deny by default (secure).
    # This is not a configuration option for production, but may be useful for testing.
    fail_safe_deny: bool = True
