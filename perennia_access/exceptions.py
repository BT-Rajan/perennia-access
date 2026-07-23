"""
Authorization exceptions.

All public operations raise a Perennia access exception or subclass.
No raw database, SQL, or framework exceptions escape the public API.

Three classes of failure:
- AuthorizationDenied: User is authenticated but lacks permission
- InvalidAccessConfiguration: Configuration/data error (role/permission not found)
- AccessError: Infrastructure or unexpected failure (database down, etc.)
"""


class PerenniaAccessError(Exception):
    """Base error. Safe to show to clients."""
    code = "access_error"


class AuthorizationDenied(PerenniaAccessError):
    """Authenticated identity does not have the required permission."""
    code = "authorization_denied"


class PermissionNotFoundError(PerenniaAccessError):
    """Permission does not exist in the system."""
    code = "permission_not_found"


class RoleNotFoundError(PerenniaAccessError):
    """Role does not exist in the system."""
    code = "role_not_found"


class InvalidAccessConfigurationError(PerenniaAccessError):
    """Access configuration is invalid or inconsistent."""
    code = "invalid_access_configuration"


class AccessDatabaseError(PerenniaAccessError):
    """Database connection or query failure."""
    code = "access_database_error"


class InvalidIdentityError(PerenniaAccessError):
    """Identity object is invalid or cannot be processed."""
    code = "invalid_identity"


# Backward-compatible alias for the old base class name.
AccessError = PerenniaAccessError
