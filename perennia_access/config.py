"""Configuration for perennia-access."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatabaseConfig:
    """MySQL database configuration."""
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = "perennia"
    charset: str = "utf8mb4"


@dataclass(frozen=True)
class AccessConfig:
    """perennia-access configuration."""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # Fail-safe mode: if authorization cannot be evaluated,
    # should we deny or allow? Always deny by default (secure).
    # This is not a configuration option for production, but may be useful for testing.
    fail_safe_deny: bool = True
