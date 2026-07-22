"""
Data models for authorization.

All models are frozen dataclasses (immutable).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class AuthenticatedIdentity:
    """
    Authenticated identity from perennia-auth.
    
    This is the contract between perennia-auth and perennia-access.
    perennia-access expects an authenticated identity with a subject_id.
    """
    subject_id: str
    session_id: str


@dataclass(frozen=True)
class Permission:
    """
    A permission (e.g., 'customer.view', 'invoice.approve').
    
    Permissions are application-defined.
    The application decides what permissions exist.
    """
    id: str
    code: str  # e.g., 'customer.view'
    description: str
    created_at: datetime


@dataclass(frozen=True)
class Role:
    """
    A role (e.g., 'admin', 'accountant').
    
    Roles are collections of permissions.
    Users are assigned roles.
    """
    id: str
    code: str  # e.g., 'admin', 'accountant'
    description: str
    created_at: datetime


@dataclass(frozen=True)
class RolePermissionAssignment:
    """Assignment of a permission to a role."""
    id: str
    role_id: str
    permission_id: str
    assigned_at: datetime


@dataclass(frozen=True)
class UserRoleAssignment:
    """Assignment of a role to a user (subject)."""
    id: str
    subject_id: str
    role_id: str
    assigned_at: datetime


@dataclass(frozen=True)
class AccessDecision:
    """Result of an authorization check."""
    subject_id: str
    permission_code: str
    allowed: bool
    reason: Optional[str] = None
