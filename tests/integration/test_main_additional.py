# tests/integration/test_main_additional.py
"""
Additional tests for main.py endpoints to improve coverage
Tests error paths and edge cases not covered by e2e tests
"""

import pytest
from uuid import uuid4
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User
from app.models.calculation import Calculation


client = TestClient(app)


class TestMainEndpointsEdgeCases:
    """Test edge cases in main.py endpoints"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_register_invalid_data(self, db_session):
        """Test registration with invalid data triggers rollback"""
        # Missing required fields
        response = client.post(
            "/auth/register",
            json={
                "first_name": "Test",
                # Missing other required fields
            }
        )
        assert response.status_code == 422  # Validation error

    def test_register_duplicate_user(self, db_session, fake_user_data):
        """Test registration with duplicate username/email"""
        fake_user_data['password'] = "TestPass123!"
        fake_user_data['confirm_password'] = "TestPass123!"
        
        # First registration
        response1 = client.post("/auth/register", json=fake_user_data)
        assert response1.status_code == 201
        
        # Duplicate registration
        response2 = client.post("/auth/register", json=fake_user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/auth/login",
            json={
                "username": "nonexistent",
                "password": "WrongPass123!"
            }
        )
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_form_endpoint(self, db_session, fake_user_data):
        """Test OAuth2 form login endpoint for Swagger UI"""
        # Register user first
        fake_user_data['password'] = "TestPass123!"
        fake_user_data['confirm_password'] = "TestPass123!"
        User.register(db_session, fake_user_data)
        db_session.commit()
        
        # Login using form data
        response = client.post(
            "/auth/token",
            data={  # Note: 'data' not 'json' for form endpoint
                "username": fake_user_data['username'],
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_create_calculation_invalid_uuid(self, db_session, fake_user_data):
        """Test calculation creation with error"""
        # Register and login
        fake_user_data['password'] = "TestPass123!"
        fake_user_data['confirm_password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        # Try to create calculation with invalid type
        response = client.post(
            "/calculations",
            json={
                "type": "invalid_operation",
                "inputs": [1, 2]
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422

    def test_get_calculation_invalid_uuid_format(self, db_session, fake_user_data):
        """Test getting calculation with invalid UUID format"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/calculations/not-a-valid-uuid",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Invalid calculation id format" in response.json()["detail"]

    def test_get_calculation_not_found(self, db_session, fake_user_data):
        """Test getting non-existent calculation"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        fake_uuid = str(uuid4())
        
        response = client.get(
            f"/calculations/{fake_uuid}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_calculation_invalid_uuid(self, db_session, fake_user_data):
        """Test updating calculation with invalid UUID"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        response = client.put(
            "/calculations/invalid-uuid",
            json={"inputs": [5, 5]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Invalid calculation id format" in response.json()["detail"]

    def test_update_calculation_not_found(self, db_session, fake_user_data):
        """Test updating non-existent calculation"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        fake_uuid = str(uuid4())
        
        response = client.put(
            f"/calculations/{fake_uuid}",
            json={"inputs": [5, 5]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_update_calculation_with_inputs(self, db_session, fake_user_data):
        """Test updating calculation inputs"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        # Create calculation
        calc = Calculation.create("addition", user.id, [2, 3])
        calc.result = calc.get_result()
        db_session.add(calc)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        # Update calculation
        response = client.put(
            f"/calculations/{calc.id}",
            json={"inputs": [10, 20]},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["result"] == 30  # 10 + 20

    def test_delete_calculation_invalid_uuid(self, db_session, fake_user_data):
        """Test deleting calculation with invalid UUID"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        response = client.delete(
            "/calculations/not-valid-uuid",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

    def test_delete_calculation_not_found(self, db_session, fake_user_data):
        """Test deleting non-existent calculation"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        fake_uuid = str(uuid4())
        
        response = client.delete(
            f"/calculations/{fake_uuid}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

    def test_list_calculations_empty(self, db_session, fake_user_data):
        """Test listing calculations when user has none"""
        fake_user_data['password'] = "TestPass123!"
        user = User.register(db_session, fake_user_data)
        db_session.commit()
        
        token = User.create_access_token({"sub": str(user.id)})
        
        response = client.get(
            "/calculations",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_login_timezone_aware_expires_at(self, db_session, fake_user_data):
        """Test that login returns timezone-aware expires_at"""
        fake_user_data['password'] = "TestPass123!"
        fake_user_data['confirm_password'] = "TestPass123!"
        User.register(db_session, fake_user_data)
        db_session.commit()
        
        response = client.post(
            "/auth/login",
            json={
                "username": fake_user_data['username'],
                "password": "TestPass123!"
            }
        )
        assert response.status_code == 200
        
        # Verify expires_at is present and formatted correctly
        data = response.json()
        assert "expires_at" in data
        # Should be ISO format timestamp
        expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
        assert expires_at.tzinfo is not None
