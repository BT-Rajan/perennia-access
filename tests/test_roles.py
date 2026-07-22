"""Tests for role management."""

import pytest
from perennia_access import RoleNotFoundError, PermissionNotFoundError


class TestRoleManagement:
    """Test role creation and retrieval."""
    
    def test_create_role(self, setup_sample_data):
        """Creating a role should store it and allow retrieval."""
        access = setup_sample_data
        
        role = access.create_role("manager", "Can manage resources")
        
        assert role.code == "manager"
        assert role.description == "Can manage resources"
        assert role.id is not None
    
    def test_get_role_by_code(self, setup_sample_data):
        """Getting a role by code should return the role."""
        access = setup_sample_data
        
        role = access.get_role("viewer")
        
        assert role is not None
        assert role.code == "viewer"
    
    def test_get_role_returns_none_for_nonexistent_role(self, setup_sample_data):
        """Getting a non-existent role should return None."""
        access = setup_sample_data
        
        role = access.get_role("nonexistent")
        
        assert role is None
    
    def test_list_roles(self, setup_sample_data):
        """Listing roles should return all roles."""
        access = setup_sample_data
        
        roles = access.list_roles()
        
        role_codes = [r.code for r in roles]
        assert "viewer" in role_codes
        assert "editor" in role_codes
        assert "accountant" in role_codes


class TestRolePermissionAssignment:
    """Test assigning permissions to roles."""
    
    def test_assign_permission_to_role(self, setup_sample_data):
        """Assigning permission to role should work."""
        access = setup_sample_data
        access.create_role("new_role", "New role")
        access.create_permission("new.permission", "New permission")
        
        access.assign_permission_to_role("new_role", "new.permission")
        
        permissions = access.get_role_permissions("new_role")
        assert "new.permission" in permissions
    
    def test_assign_permission_to_role_raises_role_not_found(self, setup_sample_data):
        """Assigning to non-existent role should raise RoleNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(RoleNotFoundError):
            access.assign_permission_to_role("nonexistent", "customer.view")
    
    def test_assign_permission_to_role_raises_permission_not_found(self, setup_sample_data):
        """Assigning non-existent permission should raise PermissionNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(PermissionNotFoundError):
            access.assign_permission_to_role("viewer", "nonexistent.permission")
    
    def test_unassign_permission_from_role(self, setup_sample_data):
        """Unassigning permission from role should work."""
        access = setup_sample_data
        
        # viewer initially has customer.view
        permissions_before = access.get_role_permissions("viewer")
        assert "customer.view" in permissions_before
        
        # Unassign it
        result = access.unassign_permission_from_role("viewer", "customer.view")
        
        assert result is True
        permissions_after = access.get_role_permissions("viewer")
        assert "customer.view" not in permissions_after
    
    def test_unassign_permission_returns_false_for_nonexistent_assignment(self, setup_sample_data):
        """Unassigning non-existent assignment should return False."""
        access = setup_sample_data
        
        result = access.unassign_permission_from_role("viewer", "invoice.approve")
        
        assert result is False
    
    def test_unassign_permission_raises_role_not_found(self, setup_sample_data):
        """Unassigning from non-existent role should raise RoleNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(RoleNotFoundError):
            access.unassign_permission_from_role("nonexistent", "customer.view")
    
    def test_unassign_permission_raises_permission_not_found(self, setup_sample_data):
        """Unassigning non-existent permission should raise PermissionNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(PermissionNotFoundError):
            access.unassign_permission_from_role("viewer", "nonexistent.permission")
    
    def test_get_role_permissions(self, setup_sample_data):
        """Getting role permissions should return all assigned permissions."""
        access = setup_sample_data
        
        permissions = access.get_role_permissions("viewer")
        
        assert set(permissions) == {"customer.view", "invoice.view"}
    
    def test_get_role_permissions_raises_role_not_found(self, setup_sample_data):
        """Getting permissions for non-existent role should raise RoleNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(RoleNotFoundError):
            access.get_role_permissions("nonexistent")


class TestUserRoleAssignment:
    """Test assigning roles to users."""
    
    def test_assign_role_to_user(self, setup_sample_data, sample_identity):
        """Assigning role to user should work."""
        access = setup_sample_data
        
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        roles = access.get_identity_roles(sample_identity)
        assert "viewer" in roles
    
    def test_assign_role_to_user_raises_role_not_found(self, setup_sample_data, sample_identity):
        """Assigning non-existent role should raise RoleNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(RoleNotFoundError):
            access.assign_role_to_user(sample_identity.subject_id, "nonexistent")
    
    def test_unassign_role_from_user(self, setup_sample_data, sample_identity):
        """Unassigning role from user should work."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        result = access.unassign_role_from_user(sample_identity.subject_id, "viewer")
        
        assert result is True
        roles = access.get_identity_roles(sample_identity)
        assert "viewer" not in roles
    
    def test_unassign_role_returns_false_for_nonexistent_assignment(self, setup_sample_data, sample_identity):
        """Unassigning non-existent assignment should return False."""
        access = setup_sample_data
        
        result = access.unassign_role_from_user(sample_identity.subject_id, "viewer")
        
        assert result is False
    
    def test_unassign_role_raises_role_not_found(self, setup_sample_data, sample_identity):
        """Unassigning non-existent role should raise RoleNotFoundError."""
        access = setup_sample_data
        
        with pytest.raises(RoleNotFoundError):
            access.unassign_role_from_user(sample_identity.subject_id, "nonexistent")
