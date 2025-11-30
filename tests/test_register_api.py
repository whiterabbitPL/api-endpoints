import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from flask import Flask

sys.path.append(str(Path(__file__).resolve().parents[1]))
from main import register_routes 

@pytest.fixture
def client():
    app = Flask(__name__)
    register_routes(app) 
    with app.test_client() as client:
        yield client

def test_register_endpoint_mocked_redis(client):
    user_id = "test_user_123"

    # Patchujemy cache (Redis client) w module main
    with patch("main.cache") as mock_cache:
        mock_cache.set = MagicMock()
        mock_cache.ttl = MagicMock(return_value=3600)
        
        def get_side_effect(key):
            if key == user_id:
                return b"mock-guid-123"
            if key in ["mock-guid-123-search-context", "mock-guid-123-account-details"]:
                return b"mock-guid-123"
            return None
        mock_cache.get = MagicMock(side_effect=get_side_effect)

        # Wywołanie endpointu
        response = client.post("/api/register", json={"user_id": user_id})
        assert response.status_code == 200

        data = response.get_json()
        assert "guid" in data
        returned_guid = data["guid"]
        assert returned_guid == "mock-guid-123"

        # Sprawdzenie wywołań set
        expected_calls = [
            ((user_id, returned_guid, 3600),),
            ((f"{returned_guid}-search-context", returned_guid, 3600),),
            ((f"{returned_guid}-account-details", returned_guid, 3600),),
        ]
        actual_calls = mock_cache.set.call_args_list
        for expected_call in expected_calls:
            assert expected_call in actual_calls

        # Sprawdzenie TTL
        assert mock_cache.ttl(user_id) == 3600
        assert mock_cache.ttl(f"{returned_guid}-search-context") == 3600
        assert mock_cache.ttl(f"{returned_guid}-account-details") == 3600
