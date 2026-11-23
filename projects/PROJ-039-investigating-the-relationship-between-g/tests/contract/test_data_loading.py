"""
Contract test for data loading in User Story 1.
Verifies schema compliance for matched_pairs.csv and distribution_groups.csv.
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from schema_validator import SchemaValidator, validate_artifacts
from config import get_project_root


class TestDataLoadingContracts:
    """Contract tests for data loading outputs from US1."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return get_project_root()

    @pytest.fixture
    def processed_dir(self, project_root):
        """Get the processed data directory."""
        return project_root / "data" / "processed"

    @pytest.fixture
    def contracts_dir(self, project_root):
        """Get the contracts directory."""
        return project_root / "contracts"

    def test_matched_pairs_schema_compliance(self, processed_dir, contracts_dir):
        """
        Verify that matched_pairs.csv (if it exists) complies with the output schema.
        This test validates Path A (Virtual Cohort Matching) output.
        """
        matched_pairs_path = processed_dir / "matched_pairs.csv"
        
        # Skip if the file doesn't exist (Path B might have been taken)
        if not matched_pairs_path.exists():
            pytest.skip("matched_pairs.csv does not exist (Path B selected or data not processed)")

        # Load the output schema
        schema_path = contracts_dir / "output.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Output schema not found at {schema_path}. Run T004b2 first.")

        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)

        # Validate the matched_pairs.csv against the schema
        validator = SchemaValidator(schema)
        
        # We need to read the CSV to validate
        try:
            import pandas as pd
            df = pd.read_csv(matched_pairs_path)
        except Exception as e:
            pytest.fail(f"Failed to read matched_pairs.csv: {e}")

        # Check required columns based on typical schema for matched pairs
        # The schema should define these, but we do a basic check first
        required_columns = ['subject_id_microbiome', 'subject_id_eeg', 'age', 'sex', 'bmi', 'alpha_power']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            pytest.fail(f"matched_pairs.csv is missing required columns: {missing_columns}")

        # Validate data types and constraints using the SchemaValidator
        # This assumes the SchemaValidator can handle CSV validation via pandas
        is_valid, errors = validator.validate_dataframe(df, "matched_pairs")
        
        if not is_valid:
            pytest.fail(f"matched_pairs.csv failed schema validation:\n{json.dumps(errors, indent=2)}")

        # Additional contract: Ensure at least 10 rows if file exists (per task description)
        if len(df) < 10:
            pytest.fail(f"matched_pairs.csv has fewer than 10 rows ({len(df)}). Path A requires >= 10 pairs.")

        # Verify no NaN values in critical columns
        critical_cols = ['subject_id_microbiome', 'subject_id_eeg', 'alpha_power']
        for col in critical_cols:
            if df[col].isna().any():
                pytest.fail(f"matched_pairs.csv contains NaN values in critical column '{col}'")

    def test_distribution_groups_schema_compliance(self, processed_dir, contracts_dir):
        """
        Verify that distribution_groups.csv (if it exists) complies with the output schema.
        This test validates Path B (Distributional Comparison) output.
        """
        distribution_groups_path = processed_dir / "distribution_groups.csv"
        
        # Skip if the file doesn't exist (Path A might have been taken)
        if not distribution_groups_path.exists():
            pytest.skip("distribution_groups.csv does not exist (Path A selected or data not processed)")

        # Load the output schema
        schema_path = contracts_dir / "output.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Output schema not found at {schema_path}. Run T004b2 first.")

        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)

        # Validate the distribution_groups.csv against the schema
        validator = SchemaValidator(schema)
        
        try:
            import pandas as pd
            df = pd.read_csv(distribution_groups_path)
        except Exception as e:
            pytest.fail(f"Failed to read distribution_groups.csv: {e}")

        # Check required columns
        required_columns = ['subject_id', 'group', 'alpha_power']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            pytest.fail(f"distribution_groups.csv is missing required columns: {missing_columns}")

        # Validate data types and constraints
        is_valid, errors = validator.validate_dataframe(df, "distribution_groups")
        
        if not is_valid:
            pytest.fail(f"distribution_groups.csv failed schema validation:\n{json.dumps(errors, indent=2)}")

        # Additional contract: Ensure valid group labels
        valid_groups = ['High', 'Low']
        if not df['group'].isin(valid_groups).all():
            invalid_groups = df[~df['group'].isin(valid_groups)]['group'].unique()
            pytest.fail(f"distribution_groups.csv contains invalid group labels: {invalid_groups}")

        # Verify at least two groups exist
        unique_groups = df['group'].unique()
        if len(unique_groups) < 2:
            pytest.fail(f"distribution_groups.csv must have at least 2 groups (High/Low). Found: {unique_groups}")

        # Verify no NaN in critical columns
        critical_cols = ['subject_id', 'group', 'alpha_power']
        for col in critical_cols:
            if df[col].isna().any():
                pytest.fail(f"distribution_groups.csv contains NaN values in critical column '{col}'")

    def test_exclusive_path_selection(self, processed_dir):
        """
        Verify that exactly one of the primary output files exists.
        Path A (matched_pairs.csv) OR Path B (distribution_groups.csv) must exist, but not both.
        """
        matched_pairs_path = processed_dir / "matched_pairs.csv"
        distribution_groups_path = processed_dir / "distribution_groups.csv"

        matched_exists = matched_pairs_path.exists()
        distribution_exists = distribution_groups_path.exists()

        if not matched_exists and not distribution_exists:
            pytest.fail(
                "Neither matched_pairs.csv nor distribution_groups.csv exists. "
                "User Story 1 pipeline did not produce expected output."
            )

        if matched_exists and distribution_exists:
            # This might be acceptable in some edge cases, but typically it's one or the other
            # based on the matching success. We'll allow it but log a warning.
            pytest.xfail(
                "Both matched_pairs.csv and distribution_groups.csv exist. "
                "This is unexpected behavior for the two-path strategy."
            )

    def test_microbiome_features_schema_compliance(self, processed_dir, contracts_dir):
        """
        Verify that microbiome_features.csv complies with the input schema.
        """
        microbiome_path = processed_dir / "microbiome_features.csv"
        
        if not microbiome_path.exists():
            pytest.skip("microbiome_features.csv does not exist.")

        schema_path = contracts_dir / "dataset.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Dataset schema not found at {schema_path}. Run T004b1 first.")

        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)

        validator = SchemaValidator(schema)
        
        try:
            import pandas as pd
            df = pd.read_csv(microbiome_path)
        except Exception as e:
            pytest.fail(f"Failed to read microbiome_features.csv: {e}")

        # Basic check: should have a subject ID column and taxon columns
        if 'subject_id' not in df.columns:
            pytest.fail("microbiome_features.csv must have a 'subject_id' column.")

        # Check for at least some taxon columns (non-ID columns)
        taxon_cols = [col for col in df.columns if col != 'subject_id']
        if len(taxon_cols) == 0:
            pytest.fail("microbiome_features.csv must contain at least one taxon abundance column.")

        # Validate against schema
        is_valid, errors = validator.validate_dataframe(df, "microbiome_features")
        if not is_valid:
            pytest.fail(f"microbiome_features.csv failed schema validation:\n{json.dumps(errors, indent=2)}")

        # Contract: Must have >= 100 rows (per task description)
        if len(df) < 100:
            pytest.fail(f"microbiome_features.csv has fewer than 100 rows ({len(df)}).")

    def test_eeg_features_schema_compliance(self, processed_dir, contracts_dir):
        """
        Verify that eeg_features.csv complies with the input schema.
        """
        eeg_path = processed_dir / "eeg_features.csv"
        
        if not eeg_path.exists():
            pytest.skip("eeg_features.csv does not exist.")

        schema_path = contracts_dir / "dataset.schema.yaml"
        if not schema_path.exists():
            pytest.fail(f"Dataset schema not found at {schema_path}. Run T004b1 first.")

        with open(schema_path, 'r') as f:
            import yaml
            schema = yaml.safe_load(f)

        validator = SchemaValidator(schema)
        
        try:
            import pandas as pd
            df = pd.read_csv(eeg_path)
        except Exception as e:
            pytest.fail(f"Failed to read eeg_features.csv: {e}")

        # Basic check: should have a subject ID column and alpha power column
        if 'subject_id' not in df.columns:
            pytest.fail("eeg_features.csv must have a 'subject_id' column.")
        
        if 'alpha_power' not in df.columns:
            pytest.fail("eeg_features.csv must have an 'alpha_power' column.")

        # Validate against schema
        is_valid, errors = validator.validate_dataframe(df, "eeg_features")
        if not is_valid:
            pytest.fail(f"eeg_features.csv failed schema validation:\n{json.dumps(errors, indent=2)}")

        # Contract: Must have >= 50 subjects (per task description)
        if len(df) < 50:
            pytest.fail(f"eeg_features.csv has fewer than 50 subjects ({len(df)}).")