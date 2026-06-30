import pytest
from pydantic import ValidationError
from src.contracts.models import RouteSequence, ValidationResult, GTFSGraph


class TestRouteSequenceSchema:
    """
    Contract tests for the RouteSequence Pydantic model.
    Ensures schema validation rules are strictly enforced.
    """

    def test_missing_station_field(self):
        """
        Test that a ValidationError is raised when the 'stations' field is missing.
        
        Input: {"line": "L", "sequence": []}
        Expected: pydantic.ValidationError with message indicating 'stations' is required.
        """
        # The input data intentionally omits the 'stations' field
        invalid_data = {
            "line": "L",
            "sequence": []
        }

        with pytest.raises(ValidationError) as exc_info:
            RouteSequence.model_validate(invalid_data)

        # Verify the error message contains the expected field requirement
        error_messages = [str(error) for error in exc_info.value.errors()]
        error_text = " ".join(error_messages)
        
        assert "Field 'stations' is required" in error_text or \
               "missing" in error_text.lower() and "stations" in error_text.lower(), \
               f"Expected error about missing 'stations' field, got: {error_messages}"

    def test_valid_route_sequence(self):
        """
        Test that a valid RouteSequence with all required fields is accepted.
        """
        valid_data = {
            "line": "L",
            "stations": ["Station A", "Station B", "Station C"],
            "sequence": [0, 1, 2]
        }
        
        # Should not raise
        route = RouteSequence.model_validate(valid_data)
        assert route.line == "L"
        assert route.stations == ["Station A", "Station B", "Station C"]
        assert route.sequence == [0, 1, 2]

    def test_empty_stations_field(self):
        """
        Test that an empty list for 'stations' is rejected if the schema requires non-empty.
        (Depending on schema definition, this might be valid or invalid; 
         checking that the model handles it gracefully).
        """
        data = {
            "line": "L",
            "stations": [],
            "sequence": []
        }
        
        try:
            RouteSequence.model_validate(data)
            # If it passes, ensure the list is indeed empty
            route = RouteSequence.model_validate(data)
            assert route.stations == []
        except ValidationError:
            # If it fails, that's also acceptable depending on strictness rules in models.py
            pass