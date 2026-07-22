"""Tests for authorization decisions."""

import pytest
from perennia_access import (
    AuthorizationDenied,
    PermissionNotFoundError,
    InvalidIdentityError,
)


class TestAuthorizationChecks:
    """Test authorization check methods."""
    
    def test_can_returns_true_when_user_has_permission(self, setup_sample_data, sample_identity):
        """User with permission should return True."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        assert access.can(sample_identity, "customer.view") is True
    
    def test_can_returns_false_when_user_lacks_permission(self, setup_sample_data, sample_identity):
        """User without permission should return False."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        assert access.can(sample_identity, "customer.edit") is False
    
    def test_can_returns_false_when_user_has_no_roles(self, setup_sample_data, sample_identity):
        """User with no roles should return False."""
        access = setup_sample_data
        
        assert access.can(sample_identity, "customer.view") is False
    
    def test_can_raises_permission_not_found_for_invalid_permission(self, setup_sample_data, sample_identity):
        """Requesting non-existent permission should raise PermissionNotFoundError."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        with pytest.raises(PermissionNotFoundError):
            access.can(sample_identity, "nonexistent.permission")
    
    def test_can_raises_invalid_identity_for_none_subject_id(self, setup_sample_data, sample_identity):
        """Identity without subject_id should raise InvalidIdentityError."""
        access = setup_sample_data
        invalid_identity = sample_identity._replace(subject_id=None)
        
        with pytest.raises(InvalidIdentityError):
            access.can(invalid_identity, "customer.view")
    
    def test_require_does_not_raise_when_user_has_permission(self, setup_sample_data, sample_identity):
        """require() should not raise when user has permission."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        # Should not raise
        access.require(sample_identity, "customer.view")
    
    def test_require_raises_authorization_denied_when_user_lacks_permission(self, setup_sample_data, sample_identity):
        """require() should raise AuthorizationDenied when user lacks permission."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        with pytest.raises(AuthorizationDenied):
            access.require(sample_identity, "customer.edit")
    
    def test_require_raises_authorization_denied_when_user_has_no_roles(self, setup_sample_data, sample_identity):
        """require() should raise AuthorizationDenied when user has no roles."""
        access = setup_sample_data
        
        with pytest.raises(AuthorizationDenied):
            access.require(sample_identity, "customer.view")
    
    def test_require_raises_permission_not_found_for_invalid_permission(self, setup_sample_data, sample_identity):
        """require() should raise PermissionNotFoundError for non-existent permission."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        
        with pytest.raises(PermissionNotFoundError):
            access.require(sample_identity, "nonexistent.permission")


class TestMultipleRoles:
    """Test authorization with multiple roles."""
    
    def test_user_with_multiple_roles_has_combined_permissions(self, setup_sample_data, sample_identity):
        """User with multiple roles should have permissions from all roles."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        access.assign_role_to_user(sample_identity.subject_id, "editor")
        
        # viewer has customer.view and invoice.view
        assert access.can(sample_identity, "customer.view") is True
        assert access.can(sample_identity, "invoice.view") is True
        
        # editor adds customer.edit
        assert access.can(sample_identity, "customer.edit") is True
        
        # but accountant permissions should still be denied
        assert access.can(sample_identity, "invoice.approve") is False
    
    def test_get_identity_permissions_with_multiple_roles(self, setup_sample_data, sample_identity):
        """get_identity_permissions() should return combined permissions from all roles."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        access.assign_role_to_user(sample_identity.subject_id, "accountant")
        
        permissions = access.get_identity_permissions(sample_identity)
        
        # Should have permissions from both viewer and accountant
        assert set(permissions) == {
            "customer.view",
            "invoice.view",
            "invoice.approve",
        }
    
    def test_get_identity_roles_returns_all_assigned_roles(self, setup_sample_data, sample_identity):
        """get_identity_roles() should return all assigned roles."""
        access = setup_sample_data
        access.assign_role_to_user(sample_identity.subject_id, "viewer")
        access.assign_role_to_user(sample_identity.subject_id, "editor")
        
        roles = access.get_identity_roles(sample_identity)
        
        assert set(roles) == {"viewer", "editor"}


class TestErrorConditions:
    """Test error handling."""
    
    def test_get_identity_permissions_raises_invalid_identity(self, setup_sample_data, sample_identity):
        """get_identity_permissions() should raise InvalidIdentityError for invalid identity."""
        access = setup_sample_data
        invalid_identity = sample_identity._replace(subject_id=None)
        
        with pytest.raises(InvalidIdentityError):
            access.get_identity_permissions(invalid_identity)
    
    def test_get_identity_roles_raises_invalid_identity(self, setup_sample_data, sample_identity):
        """get_identity_roles() should raise InvalidIdentityError for invalid identity."""
        access = setup_sample_data
        invalid_identity = sample_identity._replace(subject_id=None)
        
        with pytest.raises(InvalidIdentityError):
            access.get_identity_roles(invalid_identity)
    
    def test_get_identity_permissions_returns_empty_for_user_with_no_roles(self, setup_sample_data, sample_identity):
        """get_identity_permissions() should return empty list for user with no roles."""
        access = setup_sample_data
        
        permissions = access.get_identity_permissions(sample_identity)
        
        assert permissions == []
    
    def test_get_identity_roles_returns_empty_for_user_with_no_roles(self, setup_sample_data, sample_identity):
        """get_identity_roles() should return empty list for user with no roles."""
        access = setup_sample_data
        
        roles = access.get_identity_roles(sample_identity)
        
        assert roles == []
