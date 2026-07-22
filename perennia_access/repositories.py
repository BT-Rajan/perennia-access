"""Data access layer for authorization entities."""

from datetime import datetime
from typing import Optional, List
from .db import Database
from .models import Permission, Role, RolePermissionAssignment, UserRoleAssignment
from .exceptions import (
    AccessDatabaseError,
    PermissionNotFoundError,
    RoleNotFoundError,
)


class PermissionRepository:
    """Repository for permissions."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_code(self, code: str) -> Optional[Permission]:
        """Get a permission by its code."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM permissions WHERE code = %s",
            (code,)
        )
        if not results:
            return None
        row = results[0]
        return Permission(
            id=row["id"],
            code=row["code"],
            description=row["description"],
            created_at=row["created_at"],
        )
    
    def get_by_id(self, permission_id: str) -> Optional[Permission]:
        """Get a permission by ID."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM permissions WHERE id = %s",
            (permission_id,)
        )
        if not results:
            return None
        row = results[0]
        return Permission(
            id=row["id"],
            code=row["code"],
            description=row["description"],
            created_at=row["created_at"],
        )
    
    def list_all(self) -> List[Permission]:
        """List all permissions."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM permissions ORDER BY code"
        )
        return [
            Permission(
                id=row["id"],
                code=row["code"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in results
        ]
    
    def create(self, code: str, description: str) -> Permission:
        """Create a new permission."""
        permission_id = str(self.db.execute_insert(
            "INSERT INTO permissions (code, description, created_at) VALUES (%s, %s, %s)",
            (code, description, datetime.utcnow())
        ))
        created_permission = self.get_by_id(permission_id)
        if not created_permission:
            raise AccessDatabaseError("Failed to retrieve created permission")
        return created_permission


class RoleRepository:
    """Repository for roles."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_by_code(self, code: str) -> Optional[Role]:
        """Get a role by its code."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM roles WHERE code = %s",
            (code,)
        )
        if not results:
            return None
        row = results[0]
        return Role(
            id=row["id"],
            code=row["code"],
            description=row["description"],
            created_at=row["created_at"],
        )
    
    def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get a role by ID."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM roles WHERE id = %s",
            (role_id,)
        )
        if not results:
            return None
        row = results[0]
        return Role(
            id=row["id"],
            code=row["code"],
            description=row["description"],
            created_at=row["created_at"],
        )
    
    def list_all(self) -> List[Role]:
        """List all roles."""
        results = self.db.execute(
            "SELECT id, code, description, created_at FROM roles ORDER BY code"
        )
        return [
            Role(
                id=row["id"],
                code=row["code"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in results
        ]
    
    def create(self, code: str, description: str) -> Role:
        """Create a new role."""
        role_id = str(self.db.execute_insert(
            "INSERT INTO roles (code, description, created_at) VALUES (%s, %s, %s)",
            (code, description, datetime.utcnow())
        ))
        created_role = self.get_by_id(role_id)
        if not created_role:
            raise AccessDatabaseError("Failed to retrieve created role")
        return created_role


class RolePermissionRepository:
    """Repository for role-permission assignments."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_permissions_for_role(self, role_id: str) -> List[Permission]:
        """Get all permissions assigned to a role."""
        results = self.db.execute(
            """
            SELECT p.id, p.code, p.description, p.created_at
            FROM permissions p
            INNER JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = %s
            ORDER BY p.code
            """,
            (role_id,)
        )
        return [
            Permission(
                id=row["id"],
                code=row["code"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in results
        ]
    
    def get_roles_for_permission(self, permission_id: str) -> List[Role]:
        """Get all roles that have a permission."""
        results = self.db.execute(
            """
            SELECT r.id, r.code, r.description, r.created_at
            FROM roles r
            INNER JOIN role_permissions rp ON r.id = rp.role_id
            WHERE rp.permission_id = %s
            ORDER BY r.code
            """,
            (permission_id,)
        )
        return [
            Role(
                id=row["id"],
                code=row["code"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in results
        ]
    
    def assign(self, role_id: str, permission_id: str) -> RolePermissionAssignment:
        """Assign a permission to a role."""
        assignment_id = str(self.db.execute_insert(
            """
            INSERT INTO role_permissions (role_id, permission_id, assigned_at)
            VALUES (%s, %s, %s)
            """,
            (role_id, permission_id, datetime.utcnow())
        ))
        results = self.db.execute(
            "SELECT role_id, permission_id, assigned_at FROM role_permissions WHERE id = %s",
            (assignment_id,)
        )
        row = results[0]
        return RolePermissionAssignment(
            id=assignment_id,
            role_id=row["role_id"],
            permission_id=row["permission_id"],
            assigned_at=row["assigned_at"],
        )
    
    def unassign(self, role_id: str, permission_id: str) -> bool:
        """Unassign a permission from a role."""
        affected = self.db.execute_delete(
            "DELETE FROM role_permissions WHERE role_id = %s AND permission_id = %s",
            (role_id, permission_id)
        )
        return affected > 0


class UserRoleRepository:
    """Repository for user-role assignments."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def get_roles_for_user(self, subject_id: str) -> List[Role]:
        """Get all roles assigned to a user (subject)."""
        results = self.db.execute(
            """
            SELECT r.id, r.code, r.description, r.created_at
            FROM roles r
            INNER JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.subject_id = %s
            ORDER BY r.code
            """,
            (subject_id,)
        )
        return [
            Role(
                id=row["id"],
                code=row["code"],
                description=row["description"],
                created_at=row["created_at"],
            )
            for row in results
        ]
    
    def get_users_for_role(self, role_id: str) -> List[str]:
        """Get all subject IDs assigned to a role."""
        results = self.db.execute(
            "SELECT subject_id FROM user_roles WHERE role_id = %s ORDER BY subject_id",
            (role_id,)
        )
        return [row["subject_id"] for row in results]
    
    def assign(self, subject_id: str, role_id: str) -> UserRoleAssignment:
        """Assign a role to a user (subject)."""
        assignment_id = str(self.db.execute_insert(
            """
            INSERT INTO user_roles (subject_id, role_id, assigned_at)
            VALUES (%s, %s, %s)
            """,
            (subject_id, role_id, datetime.utcnow())
        ))
        results = self.db.execute(
            "SELECT subject_id, role_id, assigned_at FROM user_roles WHERE id = %s",
            (assignment_id,)
        )
        row = results[0]
        return UserRoleAssignment(
            id=assignment_id,
            subject_id=row["subject_id"],
            role_id=row["role_id"],
            assigned_at=row["assigned_at"],
        )
    
    def unassign(self, subject_id: str, role_id: str) -> bool:
        """Unassign a role from a user (subject)."""
        affected = self.db.execute_delete(
            "DELETE FROM user_roles WHERE subject_id = %s AND role_id = %s",
            (subject_id, role_id)
        )
        return affected > 0
