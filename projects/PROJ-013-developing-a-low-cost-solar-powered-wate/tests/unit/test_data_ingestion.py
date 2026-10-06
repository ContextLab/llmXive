import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function to test
from code.data_ingestion import fetch_solar_irradiance, APIError
from code.data_ingestion import calculate_cost, MaterialProfile, GeometryConfig

@pytest.fixture
def mock_api_response():
    """Mock NASA POWER API response."""
    return {
        "properties": {
            "parameter": {
                "RSR": {
                    "2023-10-01": 550.0,
                    "2023-10-02": 560.0,
                    "2023-10-03": 540.0,
                    # Add more to simulate > 30 days or test fallback
                    "2023-10-04": None, # Test missing data handling
                    "2023-10-05": -999.0 # Test invalid value handling
                }
            }
        }
    }

def test_fetch_solar_irradiance_success(mock_api_response):
    """Test successful fetch of solar irradiance."""
    with patch('code.data_ingestion.urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(mock_api_response).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock the datetime to have a fixed range
        with patch('code.data_ingestion.datetime') as mock_dt:
            mock_dt.now.return_value = MagicMock(strftime=lambda x: "2023-10-31")
            # Simulate start date calculation
            start_date = "2023-10-01"
            end_date = "2023-10-31"
            
            # We need to mock the timedelta logic or just pass dates directly
            # The function calculates dates internally. Let's patch the call.
            # Actually, the function uses datetime.now(). Let's just pass specific dates to the function
            # by modifying the test to call with specific dates if possible, or patch the internal logic.
            # The function signature is fetch_solar_irradiance(lat, lon, start_date, end_date, api_key)
            # So we can pass dates directly.
            
            data = fetch_solar_irradiance(5.0, 10.0, start_date, end_date)
            
            assert len(data) > 0
            assert all('date' in d for d in data)
            assert all('irradiance_W_m2' in d for d in data)
            # Check that missing/invalid values are defaulted to 550
            # Find the entry for 2023-10-04
            oct_4 = next((d for d in data if d['date'] == '2023-10-04'), None)
            assert oct_4 is not None
            assert oct_4['irradiance_W_m2'] == 550.0

def test_fetch_solar_irradiance_api_error():
    """Test API error handling."""
    with patch('code.data_ingestion.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network error")
        
        with pytest.raises(APIError):
            fetch_solar_irradiance(5.0, 10.0, "2023-10-01", "2023-10-31")

def test_fetch_solar_irradiance_invalid_json():
    """Test invalid JSON response handling."""
    with patch('code.data_ingestion.urllib.request.urlopen') as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"invalid json"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(APIError):
            fetch_solar_irradiance(5.0, 10.0, "2023-10-01", "2023-10-31")

def test_calculate_cost_signature_and_positive_return():
    """
    Unit test for cost function calculation.
    Verify `calculate_cost` exists with signature 
    (materials: List[MaterialProfile], geometry: GeometryConfig) -> float 
    and asserts `calculate_cost` returns a float > 0 for valid inputs.
    """
    # Create valid mock inputs
    materials = [
        MaterialProfile(
            material_id="7429-90-5",
            name="Aluminum",
            thermal_conductivity=205.0,
            emissivity=0.09,
            specific_heat=900.0,
            density=2700.0,
            unit_price=2.50  # Price per kg
        ),
        MaterialProfile(
            material_id="7440-50-8",
            name="Copper",
            thermal_conductivity=401.0,
            emissivity=0.03,
            specific_heat=385.0,
            density=8960.0,
            unit_price=9.00  # Price per kg
        )
    ]
    
    geometry = GeometryConfig(
        geometry_id="flat_plate_1",
        geometry_type="flat_plate",
        surface_area=2.0,  # m^2
        thickness=0.002,   # m
        inclination_angle=30.0
    )

    # Call the function
    result = calculate_cost(materials, geometry)

    # Verify return type
    assert isinstance(result, float), "calculate_cost must return a float"

    # Verify positive value
    assert result > 0.0, "calculate_cost must return a value > 0 for valid inputs"

    # Verify calculation logic roughly:
    # Mass = Density * Volume (Area * Thickness)
    # Cost = Sum(Mass * Price)
    # Aluminum: 2700 * (2.0 * 0.002) * 2.50 = 2700 * 0.004 * 2.50 = 27.0
    # Copper: 8960 * (2.0 * 0.002) * 9.00 = 8960 * 0.004 * 9.00 = 322.56
    # Total ~ 349.56
    # Allow small float tolerance
    expected_approx = (2700.0 * 2.0 * 0.002 * 2.50) + (8960.0 * 2.0 * 0.002 * 9.00)
    assert abs(result - expected_approx) < 0.01, f"Calculated cost {result} does not match expected {expected_approx}"

def test_calculate_cost_empty_materials():
    """Test calculate_cost with empty materials list returns 0.0."""
    geometry = GeometryConfig(
        geometry_id="flat_plate_1",
        geometry_type="flat_plate",
        surface_area=2.0,
        thickness=0.002,
        inclination_angle=30.0
    )
    result = calculate_cost([], geometry)
    assert result == 0.0