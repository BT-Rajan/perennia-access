"""Tests for permission management."""

from perennia_access import Permission


class TestPermissionManagement:
    """Test permission creation and retrieval."""
    
    def test_create_permission(self, setup_sample_data):
        """Creating a permission should store it and allow retrieval."""
        access = setup_sample_data
        
        permission = access.create_permission("custom.action", "A custom action")
        
        assert permission.code == "custom.action"
        assert permission.description == "A custom action"
        assert permission.id is not None
        assert isinstance(permission, Permission)
    
    def test_get_permission_by_code(self, setup_sample_data):
        """Getting a permission by code should return the permission."""
        access = setup_sample_data
        
        permission = access.get_permission("customer.view")
        
        assert permission is not None
        assert permission.code == "customer.view"
    
    def test_get_permission_returns_none_for_nonexistent_permission(self, setup_sample_data):
        """Getting a non-existent permission should return None."""
        access = setup_sample_data
        
        permission = access.get_permission("nonexistent.permission")
        
        assert permission is None
    
    def test_list_permissions(self, setup_sample_data):
        """Listing permissions should return all permissions."""
        access = setup_sample_data
        
        permissions = access.list_permissions()
        
        permission_codes = [p.code for p in permissions]
        assert "customer.view" in permission_codes
        assert "customer.edit" in permission_codes
        assert "invoice.view" in permission_codes
        assert "invoice.approve" in permission_codes
