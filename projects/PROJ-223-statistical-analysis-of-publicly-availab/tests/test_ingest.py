"""
Tests for the ingest module.
Includes unit tests, integration tests, and contract tests.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path for imports if running from tests directory
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.ingest import merge_data, preprocess_fars, preprocess_noaa
from code.config import get_output_path, ensure_directories, RANDOM_SEED
from code.utils import encode_severity, interpolate_weather, find_nearest_station

# Set seed for reproducibility in tests
np.random.seed(RANDOM_SEED)

class TestSeverityEncoding:
    """Unit tests for severity encoding logic (T009)"""

    def test_encode_severity_property(self):
        """Test that property damage is encoded correctly"""
        # FARS severity codes: 1=Fatal, 2=Injury, 3=Property Damage Only
        assert encode_severity(1) == 'Fatality'
        assert encode_severity(2) == 'Injury'
        assert encode_severity(3) == 'Property'

    def test_encode_severity_invalid(self):
        """Test that invalid severity codes return None or default"""
        assert encode_severity(0) is None
        assert encode_severity(4) is None
        assert encode_severity(-1) is None

    def test_encode_severity_vectorized(self):
        """Test vectorized encoding on a pandas Series"""
        codes = pd.Series([1, 2, 3, 0, 4])
        result = codes.apply(encode_severity)
        assert result[0] == 'Fatality'
        assert result[1] == 'Injury'
        assert result[2] == 'Property'
        assert pd.isna(result[3])
        assert pd.isna(result[4])

class TestMergeLogic:
    """Integration tests for FARS/NOAA merge logic (T010)"""

    def test_merge_basic(self):
        """Test basic merge functionality with mock data"""
        # Create mock FARS data
        fars_data = pd.DataFrame({
            'ACCNUM': [1, 2, 3],
            'STATE': [6, 6, 6],  # California
            'LAT': [34.05, 36.77, 37.77],
            'LON': [-118.24, -119.41, -122.41],
            'YEAR': [2022, 2022, 2022],
            'MONTH': [1, 1, 1],
            'DAY': [15, 15, 15],
            'HOUR': [10, 14, 18],
            'SEVERITY_CD': [1, 2, 3]
        })

        # Create mock NOAA data
        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400, 1800],
            'PRCP': [0.0, 0.1, 0.0],
            'VISIB': [10.0, 5.0, 10.0],
            'TEMP': [50.0, 55.0, 52.0]
        })

        # Perform merge
        result = merge_data(fars_data, noaa_data)

        # Verify merge occurred
        assert len(result) == 3
        assert 'PRCP' in result.columns
        assert 'VISIB' in result.columns
        assert 'TEMP' in result.columns
        assert 'match_method' in result.columns

    def test_merge_time_interpolation(self):
        """Test that time interpolation is correctly marked in match_method"""
        # Create FARS data at 11:00 (between NOAA 10:00 and 14:00)
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [11],
            'SEVERITY_CD': [1]
        })

        # Create NOAA data at 10:00 and 14:00
        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400],
            'PRCP': [0.0, 0.1],
            'VISIB': [10.0, 5.0],
            'TEMP': [50.0, 55.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Verify interpolation was used
        assert len(result) == 1
        assert result['match_method'].iloc[0] == 'interpolated'

    def test_merge_nearest_hour_fallback(self):
        """Test that nearest hour is used when interpolation fails"""
        # Create FARS data at 9:00 (before first NOAA record)
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [9],
            'SEVERITY_CD': [1]
        })

        # Create NOAA data at 10:00 and 14:00
        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400],
            'PRCP': [0.0, 0.1],
            'VISIB': [10.0, 5.0],
            'TEMP': [50.0, 55.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Verify nearest hour was used
        assert len(result) == 1
        assert result['match_method'].iloc[0] == 'nearest_hour'

class TestContractValidation:
    """Contract tests verifying match_method field population (T011)"""

    def test_match_method_field_exists(self):
        """Verify that match_method field is present in merged output"""
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [10],
            'SEVERITY_CD': [1]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178'],
            'DATE': ['2022-01-15'],
            'TIME': [1000],
            'PRCP': [0.0],
            'VISIB': [10.0],
            'TEMP': [50.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Contract: match_method must exist
        assert 'match_method' in result.columns, "Contract violation: match_method field missing"

    def test_match_method_values_valid(self):
        """Verify that match_method contains only valid values"""
        fars_data = pd.DataFrame({
            'ACCNUM': [1, 2, 3],
            'STATE': [6, 6, 6],
            'LAT': [34.05, 36.77, 37.77],
            'LON': [-118.24, -119.41, -122.41],
            'YEAR': [2022, 2022, 2022],
            'MONTH': [1, 1, 1],
            'DAY': [15, 15, 15],
            'HOUR': [10, 14, 18],
            'SEVERITY_CD': [1, 2, 3]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400, 1800],
            'PRCP': [0.0, 0.1, 0.0],
            'VISIB': [10.0, 5.0, 10.0],
            'TEMP': [50.0, 55.0, 52.0]
        })

        result = merge_data(fars_data, noaa_data)

        valid_methods = {'interpolated', 'nearest_hour', 'exact_match'}
        methods = set(result['match_method'].dropna())

        # Contract: all match_method values must be valid
        invalid_methods = methods - valid_methods
        assert len(invalid_methods) == 0, f"Contract violation: invalid match_method values found: {invalid_methods}"

    def test_match_method_populated_for_all_records(self):
        """Verify that match_method is populated for every merged record"""
        fars_data = pd.DataFrame({
            'ACCNUM': [1, 2, 3],
            'STATE': [6, 6, 6],
            'LAT': [34.05, 36.77, 37.77],
            'LON': [-118.24, -119.41, -122.41],
            'YEAR': [2022, 2022, 2022],
            'MONTH': [1, 1, 1],
            'DAY': [15, 15, 15],
            'HOUR': [10, 14, 18],
            'SEVERITY_CD': [1, 2, 3]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400, 1800],
            'PRCP': [0.0, 0.1, 0.0],
            'VISIB': [10.0, 5.0, 10.0],
            'TEMP': [50.0, 55.0, 52.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Contract: match_method must not be null for any record
        null_count = result['match_method'].isnull().sum()
        assert null_count == 0, f"Contract violation: {null_count} records have null match_method"

    def test_match_method_reflects_interpolation_logic(self):
        """Verify that match_method correctly reflects when interpolation was used"""
        # Create scenario where interpolation is required
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [12],  # Between 10 and 14
            'SEVERITY_CD': [1]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178', 'USW00023178'],
            'DATE': ['2022-01-15', '2022-01-15'],
            'TIME': [1000, 1400],
            'PRCP': [0.0, 0.2],
            'VISIB': [10.0, 4.0],
            'TEMP': [50.0, 54.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Contract: interpolation should be used for mid-point
        assert result['match_method'].iloc[0] == 'interpolated', \
            "Contract violation: match_method should be 'interpolated' for mid-point time"

        # Verify interpolated values are reasonable (between the two sources)
        assert 0.0 <= result['PRCP'].iloc[0] <= 0.2
        assert 4.0 <= result['VISIB'].iloc[0] <= 10.0
        assert 50.0 <= result['TEMP'].iloc[0] <= 54.0

    def test_match_method_reflects_exact_match(self):
        """Verify that match_method is 'exact_match' when time aligns perfectly"""
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [10],
            'SEVERITY_CD': [1]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178'],
            'DATE': ['2022-01-15'],
            'TIME': [1000],  # Exact match
            'PRCP': [0.0],
            'VISIB': [10.0],
            'TEMP': [50.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Contract: exact match should be recorded
        assert result['match_method'].iloc[0] == 'exact_match', \
            "Contract violation: match_method should be 'exact_match' for perfect time alignment"

    def test_contract_schema_compliance(self):
        """Verify merged output complies with expected schema fields"""
        fars_data = pd.DataFrame({
            'ACCNUM': [1],
            'STATE': [6],
            'LAT': [34.05],
            'LON': [-118.24],
            'YEAR': [2022],
            'MONTH': [1],
            'DAY': [15],
            'HOUR': [10],
            'SEVERITY_CD': [1]
        })

        noaa_data = pd.DataFrame({
            'STATION': ['USW00023178'],
            'DATE': ['2022-01-15'],
            'TIME': [1000],
            'PRCP': [0.0],
            'VISIB': [10.0],
            'TEMP': [50.0]
        })

        result = merge_data(fars_data, noaa_data)

        # Contract: Required fields from merged_dataset.schema.yaml
        required_fields = [
            'ACCNUM', 'STATE', 'LAT', 'LON', 'YEAR', 'MONTH', 'DAY', 'HOUR',
            'SEVERITY', 'SEVERITY_CD', 'STATION', 'PRCP', 'VISIB', 'TEMP',
            'match_method'
        ]

        missing_fields = [f for f in required_fields if f not in result.columns]
        assert len(missing_fields) == 0, f"Contract violation: missing required fields: {missing_fields}"