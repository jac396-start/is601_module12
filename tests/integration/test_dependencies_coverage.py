# tests/integration/test_dependencies_coverage.py
"""
Additional tests for dependencies to improve coverage of app/auth/dependencies.py
Targets lines 37, 52-65 (edge cases in get_current_user)
"""

import pytest
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException
from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse


class TestGetCurrentUserEdgeCases:
    """Test edge cases in get_current_user dependency"""

    def test_get_current_user_none_token_data(self):
        """Test when verify_token returns None"""
        from unittest.mock import patch
        
        with patch('app.auth.dependencies.User.verify_token', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user("invalid_token")
            
            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in exc_info.value.detail

    def test_get_current_user_with_full_dict_payload(self):
        """Test with full user dict payload containing username"""
        from unittest.mock import patch
        
        full_user_data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch('app.auth.dependencies.User.verify_token', return_value=full_user_data):
            user = get_current_user("valid_token")
            
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.first_name == "Test"

    def test_get_current_user_with_minimal_dict_payload(self):
        """Test with minimal dict payload (only 'sub' key)"""
        from unittest.mock import patch
        
        minimal_data = {
            "sub": "123e4567-e89b-12d3-a456-426614174000"
        }
        
        with patch('app.auth.dependencies.User.verify_token', return_value=minimal_data):
            user = get_current_user("valid_token")
            
            assert str(user.id) == "123e4567-e89b-12d3-a456-426614174000"
            assert user.username == "unknown"
            assert user.email == "unknown@example.com"

    def test_get_current_user_with_uuid_directly(self):
        """Test when verify_token returns UUID directly (not dict)"""
        from unittest.mock import patch
        
        test_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
        
        with patch('app.auth.dependencies.User.verify_token', return_value=test_uuid):
            user = get_current_user("valid_token")
            
            assert user.id == test_uuid
            assert user.username == "unknown"
            assert user.first_name == "Unknown"

    def test_get_current_user_with_invalid_dict_structure(self):
        """Test with dict that has neither 'username' nor 'sub'"""
        from unittest.mock import patch
        
        invalid_data = {
            "some_other_key": "value"
        }
        
        with patch('app.auth.dependencies.User.verify_token', return_value=invalid_data):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user("token")
            
            assert exc_info.value.status_code == 401

    def test_get_current_user_with_invalid_type(self):
        """Test with completely wrong data type"""
        from unittest.mock import patch
        
        # Return a string instead of dict or UUID
        with patch('app.auth.dependencies.User.verify_token', return_value="just_a_string"):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user("token")
            
            assert exc_info.value.status_code == 401

    def test_get_current_user_exception_during_processing(self):
        """Test exception handling during user creation"""
        from unittest.mock import patch
        
        # Make verify_token return data that will cause UserResponse to fail
        invalid_data = {
            "username": "test",
            "id": "not-a-valid-uuid",  # Invalid UUID
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch('app.auth.dependencies.User.verify_token', return_value=invalid_data):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user("token")
            
            assert exc_info.value.status_code == 401

    def test_get_current_active_user_inactive(self):
        """Test get_current_active_user with inactive user"""
        inactive_user = UserResponse(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            username="inactive",
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            is_active=False,  # Inactive
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(inactive_user)
        
        assert exc_info.value.status_code == 400
        assert "Inactive user" in exc_info.value.detail

    def test_get_current_active_user_active(self):
        """Test get_current_active_user with active user"""
        active_user = UserResponse(
            id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            username="active",
            email="active@example.com",
            first_name="Active",
            last_name="User",
            is_active=True,  # Active
            is_verified=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        result = get_current_active_user(active_user)
        
        assert result == active_user
        assert result.is_active is True
