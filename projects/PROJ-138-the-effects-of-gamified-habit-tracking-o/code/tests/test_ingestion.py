"""
Contract tests for data ingestion pipeline (TDD Red).

This module implements T010: Contract test for schema validation and consent checks.
It asserts that the ingestion script raises ValueError under specific failure conditions
before the full implementation is complete.
"""
import os
import pytest
import tempfile
import shutil
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the functions we are testing against
# Note: These imports rely on the implementation in code/data/validation.py and code/data/ingestion.py
# If the implementation is missing, these imports might fail or the functions won't behave as expected,
# which is the "Red" part of TDD.
try:
    from code.data.validation import check_consent, validate_schema
    from code.data.ingestion import load_data
    from code.data.synthetic_generator import OUTPUT_PATH as SYNTHETIC_PATH
    HAS_IMPLEMENTATION = True
except ImportError:
    HAS_IMPLEMENTATION = False


@pytest.mark.skipif(not HAS_IMPLEMENTATION, reason="Implementation modules not yet available")
class TestIngestionContract:
    """Contract tests for T010: Schema validation and consent checks."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.consent_dir = os.path.join(self.temp_dir, "data", "consent")
        self.raw_dir = os.path.join(self.temp_dir, "data", "raw")
        os.makedirs(self.consent_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_validation_missing_consent_real_data(self):
        """
        Assert that ingestion raises ValueError if data/consent/ is missing for real data.
        
        Context: This is a TDD Red task. The script should halt if real data is present
        but consent is missing (FR-010).
        """
        # Arrange: No consent file exists in the temporary consent directory
        # We simulate "real data" presence by ensuring no synthetic flag exists
        # and the directory is empty.
        assert not os.listdir(self.consent_dir), "Consent dir should be empty for this test"

        # Mock the environment to point to our temp directory
        with patch('code.data.validation.CONSENT_DIR', self.consent_dir):
            with patch('code.data.ingestion.RAW_DATA_DIR', self.raw_dir):
                # Act & Assert: Should raise ValueError
                with pytest.raises(ValueError, match="Missing consent"):
                    check_consent()

    def test_schema_validation_missing_columns(self):
        """
        Assert that ingestion raises ValueError if required columns are absent.
        
        Context: Validates the schema contract defined in contracts/dataset.schema.yaml.
        """
        # Arrange: Create a mock DataFrame with missing required columns
        # Required columns based on spec: User_ID, Gamified, Adherence, etc.
        incomplete_df = pd.DataFrame({
            "user_id": [1, 2],
            "date": ["2023-01-01", "2023-01-02"]
            # Missing: Gamified, Adherence, Conscientiousness, etc.
        })

        # Act & Assert: validate_schema should raise ValueError
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_schema(incomplete_df)

    def test_schema_validation_valid_data(self):
        """
        Assert that ingestion passes validation when all required columns are present.
        """
        # Arrange: Create a mock DataFrame with all required columns
        required_columns = [
            "User_ID", "Gamified", "Adherence", "Conscientiousness",
            "Need_for_Achievement", "Date", "Event_Type"
        ]
        valid_df = pd.DataFrame({col: [1] * 10 for col in required_columns})

        # Act & Assert: Should not raise
        try:
            validate_schema(valid_df)
        except ValueError:
            pytest.fail("Valid data should not raise ValueError")

    def test_ingestion_halts_on_insufficient_data(self):
        """
        Assert that load_data raises ValueError if group sizes are insufficient.
        
        Context: FR-008 requires at least 30 non-gamified users.
        """
        # Arrange: Create a dataset with insufficient non-gamified users
        # Total 100 users, but only 10 non-gamified (False)
        data = {
            "User_ID": list(range(100)),
            "Gamified": [True] * 90 + [False] * 10, # Only 10 False
            "Adherence": [1] * 100,
            "Conscientiousness": [0.5] * 100,
            "Date": ["2023-01-01"] * 100,
            "Event_Type": ["log"] * 100
        }
        df = pd.DataFrame(data)
        
        # Save to a temporary CSV to simulate raw data
        temp_csv = os.path.join(self.raw_dir, "test_data.csv")
        df.to_csv(temp_csv, index=False)

        with patch('code.data.ingestion.RAW_DATA_DIR', self.raw_dir):
            with patch('code.data.ingestion.CONSENT_DIR', self.consent_dir):
                # Create a dummy consent file to bypass consent check
                consent_file = os.path.join(self.consent_dir, "consent_record.json")
                with open(consent_file, 'w') as f:
                    f.write('{"status": "approved"}')

                # Act & Assert: load_data should raise ValueError for group imbalance
                with pytest.raises(ValueError, match="Group Imbalance|Data Insufficiency"):
                    load_data()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])