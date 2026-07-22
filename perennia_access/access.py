"""
Core authorization controller.

PerenniaAccess is the main interface for authorization decisions.
It requires perennia-auth for authenticated identity.
"""

from typing import Optional, List
from .config import AccessConfig
from .db import Database
from .models import (
    AuthenticatedIdentity,
    Permission,
    Role,
    AccessDecision,
)
from .repositories import (
    PermissionRepository,
    RoleRepository,
    RolePermissionRepository,
    UserRoleRepository,
)
from .exceptions import (
    AccessError,
    AuthorizationDenied,
    PermissionNotFoundError,
    RoleNotFoundError,
    InvalidIdentityError,
    InvalidAccessConfigurationError,
)


class PerenniaAccess:
    """
    Authorization controller for Perennia applications.
    
    Requires perennia-auth for authenticated identity.
    Backend-only authorization. No frontend code.
    No silent failures. Clear error distinction.
    
    Usage:
        access = PerenniaAccess(config)
        
        # Check authorization
        if access.can(identity, "customer.view"):
            # user has permission
        
        # Require authorization (raises if denied)
        access.require(identity, "customer.edit")
    """
    
    def __init__(self, config: AccessConfig):
        self.config = config
        self.db = Database(config.database)
        self.db.connect()
        
        self.permissions = PermissionRepository(self.db)
        self.roles = RoleRepository(self.db)
        self.role_permissions = RolePermissionRepository(self.db)
        self.user_roles = UserRoleRepository(self.db)
    
    def can(self, identity: AuthenticatedIdentity, permission_code: str) -> bool:
        """
        Check if an authenticated identity has a permission.
        
        Args:
            identity: Authenticated identity from perennia-auth
            permission_code: Permission code (e.g., 'customer.view')
        
        Returns:
            True if the identity has the permission, False otherwise.
        
        Raises:
            InvalidIdentityError: If identity is invalid
            PermissionNotFoundError: If permission does not exist
            AccessDatabaseError: If database query fails
        
        Does NOT raise AuthorizationDenied. Use require() for that.
        """
        self._validate_identity(identity)
        
        # Check that permission exists
        permission = self.permissions.get_by_code(permission_code)
        if not permission:
            raise PermissionNotFoundError(
                f"Permission '{permission_code}' does not exist"
            )
        
        # Get user's roles
        user_roles = self.user_roles.get_roles_for_user(identity.subject_id)
        if not user_roles:
            return False
        
        # Check if any role has this permission
        for role in user_roles:
            role_permissions = self.role_permissions.get_permissions_for_role(role.id)
            for role_perm in role_permissions:
                if role_perm.code == permission_code:
                    return True
        
        return False
    
    def require(self, identity: AuthenticatedIdentity, permission_code: str) -> None:
        """
        Require that an authenticated identity has a permission.
        
        Raises AuthorizationDenied if the identity lacks the permission.
        
        Args:
            identity: Authenticated identity from perennia-auth
            permission_code: Permission code (e.g., 'customer.view')
        
        Raises:
            InvalidIdentityError: If identity is invalid
            PermissionNotFoundError: If permission does not exist
            AuthorizationDenied: If identity lacks permission
            AccessDatabaseError: If database query fails
        """
        if not self.can(identity, permission_code):
            raise AuthorizationDenied(
                f"Subject {identity.subject_id} does not have permission '{permission_code}'"
            )
    
    def get_identity_permissions(self, identity: AuthenticatedIdentity) -> List[str]:
        """
        Get all permission codes that an identity has.
        
        Args:
            identity: Authenticated identity from perennia-auth
        
        Returns:
            List of permission codes the identity has through their roles.
        
        Raises:
            InvalidIdentityError: If identity is invalid
            AccessDatabaseError: If database query fails
        """
        self._validate_identity(identity)
        
        user_roles = self.user_roles.get_roles_for_user(identity.subject_id)
        
        permissions_set = set()
        for role in user_roles:
            role_permissions = self.role_permissions.get_permissions_for_role(role.id)
            for perm in role_permissions:
                permissions_set.add(perm.code)
        
        return sorted(list(permissions_set))
    
    def get_identity_roles(self, identity: AuthenticatedIdentity) -> List[str]:
        """
        Get all role codes that an identity has.
        
        Args:
            identity: Authenticated identity from perennia-auth
        
        Returns:
            List of role codes the identity has.
        
        Raises:
            InvalidIdentityError: If identity is invalid
            AccessDatabaseError: If database query fails
        """
        self._validate_identity(identity)
        return [role.code for role in self.user_roles.get_roles_for_user(identity.subject_id)]
    
    # Management APIs
    
    def create_permission(self, code: str, description: str) -> Permission:
        """Create a new permission."""
        return self.permissions.create(code, description)
    
    def get_permission(self, code: str) -> Optional[Permission]:
        """Get a permission by code."""
        return self.permissions.get_by_code(code)
    
    def list_permissions(self) -> List[Permission]:
        """List all permissions."""
        return self.permissions.list_all()
    
    def create_role(self, code: str, description: str) -> Role:
        """Create a new role."""
        return self.roles.create(code, description)
    
    def get_role(self, code: str) -> Optional[Role]:
        """Get a role by code."""
        return self.roles.get_by_code(code)
    
    def list_roles(self) -> List[Role]:
        """List all roles."""
        return self.roles.list_all()
    
    def assign_permission_to_role(self, role_code: str, permission_code: str) -> None:
        """
        Assign a permission to a role.
        
        Raises:
            RoleNotFoundError: If role does not exist
            PermissionNotFoundError: If permission does not exist
            AccessDatabaseError: If assignment fails
        """
        role = self.roles.get_by_code(role_code)
        if not role:
            raise RoleNotFoundError(f"Role '{role_code}' does not exist")
        
        permission = self.permissions.get_by_code(permission_code)
        if not permission:
            raise PermissionNotFoundError(f"Permission '{permission_code}' does not exist")
        
        self.role_permissions.assign(role.id, permission.id)
    
    def unassign_permission_from_role(self, role_code: str, permission_code: str) -> bool:
        """
        Unassign a permission from a role.
        
        Returns True if the assignment existed and was removed.
        Returns False if the assignment did not exist.
        """
        role = self.roles.get_by_code(role_code)
        if not role:
            raise RoleNotFoundError(f"Role '{role_code}' does not exist")
        
        permission = self.permissions.get_by_code(permission_code)
        if not permission:
            raise PermissionNotFoundError(f"Permission '{permission_code}' does not exist")
        
        return self.role_permissions.unassign(role.id, permission.id)
    
    def get_role_permissions(self, role_code: str) -> List[str]:
        """
        Get all permission codes for a role.
        
        Raises:
            RoleNotFoundError: If role does not exist
        """
        role = self.roles.get_by_code(role_code)
        if not role:
            raise RoleNotFoundError(f"Role '{role_code}' does not exist")
        
        permissions = self.role_permissions.get_permissions_for_role(role.id)
        return [perm.code for perm in permissions]
    
    def assign_role_to_user(self, subject_id: str, role_code: str) -> None:
        """
        Assign a role to a user (subject).
        
        Raises:
            RoleNotFoundError: If role does not exist
            AccessDatabaseError: If assignment fails
        """
        role = self.roles.get_by_code(role_code)
        if not role:
            raise RoleNotFoundError(f"Role '{role_code}' does not exist")
        
        self.user_roles.assign(subject_id, role.id)
    
    def unassign_role_from_user(self, subject_id: str, role_code: str) -> bool:
        """
        Unassign a role from a user (subject).
        
        Returns True if the assignment existed and was removed.
        Returns False if the assignment did not exist.
        """
        role = self.roles.get_by_code(role_code)
        if not role:
            raise RoleNotFoundError(f"Role '{role_code}' does not exist")
        
        return self.user_roles.unassign(subject_id, role.id)
    
    # Internal helpers
    
    def _validate_identity(self, identity: AuthenticatedIdentity) -> None:
        """Validate that an identity is properly formed."""
        if not identity or not identity.subject_id:
            raise InvalidIdentityError("Identity must have a subject_id")
    
    def __del__(self):
        """Clean up database connection on deletion."""
        self.db.disconnect()
