import pytest
from entropy.validator import validate_action_chain, validate_variants
import pandas as pd
import os
import tempfile
import json

class TestActionChainValidation:
    """Unit tests for the action chain validation logic."""

    def test_valid_chain(self):
        """Test a physically plausible action chain."""
        chain = "move grab place release"
        result = validate_action_chain(chain, "test-001")
        assert result["is_valid"] is True
        assert result["error_reason"] is None

    def test_valid_chain_with_lift(self):
        """Test a chain using lift."""
        chain = "move lift place release"
        result = validate_action_chain(chain, "test-002")
        assert result["is_valid"] is True

    def test_invalid_token(self):
        """Test a chain with an invalid action token."""
        chain = "move grab fly release"
        result = validate_action_chain(chain, "test-003")
        assert result["is_valid"] is False
        assert "fly" in result["error_reason"]

    def test_release_without_grab(self):
        """Test a chain where release happens before grab."""
        chain = "move release place"
        result = validate_action_chain(chain, "test-004")
        assert result["is_valid"] is False
        assert "release" in result["error_reason"]
        assert "prior grab" in result["error_reason"]

    def test_empty_chain(self):
        """Test an empty chain."""
        chain = ""
        result = validate_action_chain(chain, "test-005")
        assert result["is_valid"] is False
        assert "empty" in result["error_reason"].lower()

    def test_none_chain(self):
        """Test a None chain."""
        result = validate_action_chain(None, "test-006")
        assert result["is_valid"] is False

    def test_known_broken_chain(self):
        """
        Specific test case requested in task:
        'Unit test with known broken chain returns False'.
        """
        # A known broken chain: releasing without holding anything
        broken_chain = "approach release move"
        result = validate_action_chain(broken_chain, "broken-case-001")
        assert result["is_valid"] is False
        assert "release" in result["error_reason"]

class TestValidateVariantsIntegration:
    """Integration tests for the full validate_variants function."""

    def test_validate_variants_writes_output(self):
        """Test that validate_variants creates the output CSV correctly."""
        # Create a temporary directory for test files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "variants.csv")
            output_path = os.path.join(tmpdir, "validity_flags.csv")

            # Create a mock input CSV
            data = {
                "case_id": ["c1", "c2", "c3"],
                "variant_type": ["low", "medium", "high"],
                "generated_chain": [
                    "move grab place release",  # Valid
                    "move release",             # Invalid: release without grab
                    "lift place release"        # Valid
                ]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)

            # Run the validator
            validate_variants(input_path, output_path)

            # Verify output exists and has correct content
            assert os.path.exists(output_path)
            df_output = pd.read_csv(output_path)

            assert len(df_output) == 3
            assert list(df_output.columns) == ["case_id", "variant_type", "is_valid"]

            # Check specific rows
            assert df_output.iloc[0]["is_valid"] is True   # c1
            assert df_output.iloc[1]["is_valid"] is False  # c2 (broken)
            assert df_output.iloc[2]["is_valid"] is True   # c3

    def test_validate_variants_missing_column(self):
        """Test that the function fails loudly if the chain column is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "variants.csv")
            output_path = os.path.join(tmpdir, "validity_flags.csv")

            # Create a mock input CSV with WRONG column name
            data = {
                "case_id": ["c1"],
                "variant_type": ["low"],
                "wrong_chain": ["move grab"]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)

            # Expect an exception
            with pytest.raises(Exception) as excinfo:
                validate_variants(input_path, output_path)

            assert "missing required chain column" in str(excinfo.value).lower()

    def test_validate_variants_supports_action_chain_alias(self):
        """Test that the function accepts 'action_chain' column name as well."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "variants.csv")
            output_path = os.path.join(tmpdir, "validity_flags.csv")

            # Create a mock input CSV using 'action_chain'
            data = {
                "case_id": ["c1"],
                "variant_type": ["low"],
                "action_chain": ["move grab place release"]
            }
            df_input = pd.DataFrame(data)
            df_input.to_csv(input_path, index=False)

            # Should run without error
            validate_variants(input_path, output_path)

            assert os.path.exists(output_path)
            df_output = pd.read_csv(output_path)
            assert df_output.iloc[0]["is_valid"] is True