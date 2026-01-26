"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test the /activities endpoint"""

    def test_get_activities(self):
        """Test fetching all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have activities
        assert len(data) > 0
        
        # Check that expected activities exist
        assert "Basketball Team" in data
        assert "Soccer Club" in data
        assert "Art Club" in data
        
    def test_activities_structure(self):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Check first activity structure
        activity = data["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignupEndpoint:
    """Test the signup endpoint"""

    def test_signup_success(self):
        """Test successful signup"""
        email = "test@mergington.edu"
        activity = "Basketball Team"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Signup
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        assert "signed up" in response.json()["message"].lower()
        
        # Verify participant was added
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count + 1
        assert email in final_response.json()[activity]["participants"]

    def test_signup_duplicate(self):
        """Test that duplicate signups are rejected"""
        email = "duplicate@mergington.edu"
        activity = "Soccer Club"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Duplicate signup
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_invalid_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Invalid Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Test the unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister"""
        email = "unregister@mergington.edu"
        activity = "Drama Club"
        
        # Signup first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Get count before unregister
        before_response = client.get("/activities")
        before_count = len(before_response.json()[activity]["participants"])
        assert email in before_response.json()[activity]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "unregistered" in response.json()["message"].lower()
        
        # Verify participant was removed
        after_response = client.get("/activities")
        after_count = len(after_response.json()[activity]["participants"])
        assert after_count == before_count - 1
        assert email not in after_response.json()[activity]["participants"]

    def test_unregister_not_registered(self):
        """Test unregister for non-registered participant"""
        email = "notregistered@mergington.edu"
        activity = "Art Club"
        
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_invalid_activity(self):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Invalid Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestActivityCapacity:
    """Test activity capacity constraints"""

    def test_activity_has_capacity(self):
        """Test that activities have max_participants constraint"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert activity["max_participants"] > 0
            # Participants should not exceed capacity
            assert len(activity["participants"]) <= activity["max_participants"]


class TestPreexistingParticipants:
    """Test activities with pre-existing participants"""

    def test_chess_club_has_participants(self):
        """Test that Chess Club has pre-existing participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "Chess Club" in data
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) > 0
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

    def test_programming_class_has_participants(self):
        """Test that Programming Class has pre-existing participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "Programming Class" in data
        prog_class = data["Programming Class"]
        assert len(prog_class["participants"]) > 0
        assert "emma@mergington.edu" in prog_class["participants"]
        assert "sophia@mergington.edu" in prog_class["participants"]
