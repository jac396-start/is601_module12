# tests/integration/test_user_schema_validation.py
"""
Tests for user schema validation to improve coverage of app/schemas/user.py
Targets lines 53-55, 60-71, 184-188
"""

import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, PasswordUpdate


class TestUserCreatePasswordValidation:
    """Test password validation in UserCreate schema"""

    def test_password_mismatch(self):
        """Test that mismatched passwords raise ValueError"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="SecurePass123!",
                confirm_password="DifferentPass123!"
            )
        assert "Passwords do not match" in str(exc_info.value)

    def test_password_too_short(self):
        """Test password length validation"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="Short1!",
                confirm_password="Short1!"
            )
        assert "at least 8 characters" in str(exc_info.value)

    def test_password_no_uppercase(self):
        """Test password must contain uppercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="lowercase123!",
                confirm_password="lowercase123!"
            )
        assert "uppercase letter" in str(exc_info.value)

    def test_password_no_lowercase(self):
        """Test password must contain lowercase letter"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="UPPERCASE123!",
                confirm_password="UPPERCASE123!"
            )
        assert "lowercase letter" in str(exc_info.value)

    def test_password_no_digit(self):
        """Test password must contain digit"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="NoDigitsHere!",
                confirm_password="NoDigitsHere!"
            )
        assert "digit" in str(exc_info.value)

    def test_password_no_special_char(self):
        """Test password must contain special character"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                username="johndoe",
                password="NoSpecial123",
                confirm_password="NoSpecial123"
            )
        assert "special character" in str(exc_info.value)

    def test_valid_password(self):
        """Test that valid password passes all validation"""
        user = UserCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            username="johndoe",
            password="ValidPass123!",
            confirm_password="ValidPass123!"
        )
        assert user.password == "ValidPass123!"


class TestPasswordUpdateValidation:
    """Test PasswordUpdate schema validation"""

    def test_password_update_mismatch(self):
        """Test new password and confirmation must match"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordUpdate(
                current_password="OldPass123!",
                new_password="NewPass123!",
                confirm_new_password="DifferentPass123!"
            )
        assert "do not match" in str(exc_info.value)

    def test_password_update_same_as_current(self):
        """Test new password must differ from current"""
        with pytest.raises(ValidationError) as exc_info:
            PasswordUpdate(
                current_password="SamePass123!",
                new_password="SamePass123!",
                confirm_new_password="SamePass123!"
            )
        assert "must be different" in str(exc_info.value)

    def test_valid_password_update(self):
        """Test valid password update"""
        pwd_update = PasswordUpdate(
            current_password="OldPass123!",
            new_password="NewPass123!",
            confirm_new_password="NewPass123!"
        )
        assert pwd_update.current_password == "OldPass123!"
        assert pwd_update.new_password == "NewPass123!"
