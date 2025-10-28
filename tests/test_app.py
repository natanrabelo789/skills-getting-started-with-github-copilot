import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

client = TestClient(app)


class TestApp:
    def setup_method(self):
        """Reset activities before each test"""
        # Reset to original state
        activities.clear()
        activities.update({
            "Chess Club": {
                "description": "Learn strategies and compete in chess tournaments",
                "schedule": "Fridays, 3:30 PM - 5:00 PM",
                "max_participants": 12,
                "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
            },
            "Programming Class": {
                "description": "Learn programming fundamentals and build software projects",
                "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
                "max_participants": 20,
                "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
            },
            "Gym Class": {
                "description": "Physical education and sports activities",
                "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
                "max_participants": 30,
                "participants": ["john@mergington.edu", "olivia@mergington.edu"]
            }
        })

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/")
        assert response.status_code == 200

    def test_get_activities(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Check Chess Club structure
        chess_club = data["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=new_student@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Signed up new_student@mergington.edu for Chess Club"
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "new_student@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_already_registered_student(self):
        """Test that a student cannot register for multiple activities"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to signup for another activity
        response2 = client.post(
            "/activities/Programming Class/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Student is already signed up for an activity"

    def test_signup_for_same_activity_twice(self):
        """Test that a student cannot register for the same activity twice"""
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Try to signup for same activity again
        response2 = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert data["detail"] == "Student is already signed up for an activity"

    def test_unregister_from_activity_success(self):
        """Test successful unregistration from an activity"""
        # First, register a student
        client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        
        # Then unregister
        response = client.delete(
            "/activities/Chess Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Unregistered test@mergington.edu from Chess Club"
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self):
        """Test unregistration from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_student_not_registered(self):
        """Test unregistration of a student who isn't registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"

    def test_activities_have_required_fields(self):
        """Test that all activities have the required fields"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"
            
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)
            assert activity_data["max_participants"] > 0

    def test_participant_email_format(self):
        """Test that participant emails follow expected format"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        for activity_name, activity_data in data.items():
            for participant in activity_data["participants"]:
                assert "@mergington.edu" in participant, f"Participant {participant} in {activity_name} doesn't have expected email domain"

    def test_multiple_operations_flow(self):
        """Test a complete flow of operations"""
        # Get initial state
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        # Add a student
        signup_response = client.post(
            "/activities/Chess Club/signup?email=flowtest@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Verify addition
        after_signup = client.get("/activities")
        after_count = len(after_signup.json()["Chess Club"]["participants"])
        assert after_count == initial_count + 1
        
        # Remove the student
        unregister_response = client.delete(
            "/activities/Chess Club/unregister?email=flowtest@mergington.edu"
        )
        assert unregister_response.status_code == 200
        
        # Verify removal
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Chess Club"]["participants"])
        assert final_count == initial_count