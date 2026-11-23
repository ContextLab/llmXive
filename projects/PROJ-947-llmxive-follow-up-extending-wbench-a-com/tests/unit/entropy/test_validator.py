"""
Unit tests for the Action Chain Validator (T014).
"""
import pytest
import pandas as pd
import json
import tempfile
import os
from pathlib import Path

from code.entropy.validator import validate_action_chain, validate_variants, _parse_action_chain

class TestParseActionChain:
    """Tests for action chain parsing."""

    def test_parse_comma_separated(self):
        """Test parsing comma-separated actions."""
        chain = "grab, lift, move, drop"
        result = _parse_action_chain(chain)
        assert result == ["grab", "lift", "move", "drop"]

    def test_parse_space_separated(self):
        """Test parsing space-separated actions."""
        chain = "grab lift move drop"
        result = _parse_action_chain(chain)
        assert result == ["grab", "lift", "move", "drop"]

    def test_parse_json_array(self):
        """Test parsing JSON array format."""
        chain = '["grab", "lift", "move"]'
        result = _parse_action_chain(chain)
        assert result == ["grab", "lift", "move"]

    def test_parse_empty(self):
        """Test parsing empty string."""
        assert _parse_action_chain("") == []
        assert _parse_action_chain(None) == []

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string."""
        assert _parse_action_chain("   ") == []

class TestValidateActionChain:
    """Tests for action chain validation."""

    def test_valid_chain(self):
        """Test that a valid chain returns True."""
        chain = "grab, lift, move, place"
        assert validate_action_chain(chain) is True

    def test_impossible_sequence_drop_catch(self):
        """Test that drop followed by catch is invalid."""
        chain = "drop, catch"
        assert validate_action_chain(chain) is False

    def test_impossible_sequence_burn_freeze(self):
        """Test that burn followed by freeze is invalid."""
        chain = "burn, freeze"
        assert validate_action_chain(chain) is False

    def test_impossible_sequence_explode_assemble(self):
        """Test that explode followed by assemble is invalid."""
        chain = "explode, assemble"
        assert validate_action_chain(chain) is False

    def test_empty_chain_returns_false(self):
        """Test that empty chain returns False."""
        assert validate_action_chain("") is False
        assert validate_action_chain(None) is False

    def test_empty_list_returns_false(self):
        """Test that empty list returns False."""
        assert validate_action_chain("[]") is False

    def test_property_conflict_hot_cold(self):
        """Test that immediate hot/cold conflict is detected."""
        chain = "burn, freeze"
        assert validate_action_chain(chain) is False

    def test_state_violation_pattern(self):
        """Test state violation detection."""
        # broken -> repair -> break should be invalid
        chain = "broken, repair, break"
        # Note: This depends on how we parse the chain
        # If these are treated as actions, it should fail
        # We'll check the logic in the validator

    def test_missing_dependency(self):
        """Test missing dependency detection."""
        # 'throw' requires 'grab' and 'hold' beforehand
        chain = "throw"
        # This should fail because grab and hold are missing
        assert validate_action_chain(chain) is False

    def test_valid_dependency_chain(self):
        """Test valid dependency chain."""
        # grab -> hold -> lift -> throw (all dependencies met)
        chain = "grab, hold, lift, throw"
        assert validate_action_chain(chain) is True

    def test_partial_dependency_chain(self):
        """Test chain with partial dependencies."""
        # grab -> throw (missing hold)
        chain = "grab, throw"
        assert validate_action_chain(chain) is False

class TestValidateVariants:
    """Tests for the full variant validation pipeline."""

    def test_validate_variants_with_known_broken_chain(self):
        """Test that a known broken chain returns False in the output."""
        # Create a temporary input file with a broken chain
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,variant_type,action_chain\n")
            f.write("test_case_1,low,\"drop, catch\"\n")  # Impossible sequence
            f.write("test_case_2,medium,\"grab, lift, move\"\n")  # Valid
            input_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name

            try:
                result_df = validate_variants(input_path, output_path)

                # Check that the file was created
                assert os.path.exists(output_path)

                # Check the results
                assert len(result_df) == 2

                # First case should be invalid (drop -> catch)
                case_1 = result_df[result_df['case_id'] == 'test_case_1'].iloc[0]
                assert case_1['is_valid'] is False

                # Second case should be valid
                case_2 = result_df[result_df['case_id'] == 'test_case_2'].iloc[0]
                assert case_2['is_valid'] is True

            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)

        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    def test_validate_variants_empty_input(self):
        """Test validation with empty input file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,variant_type,action_chain\n")
            input_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name

            try:
                result_df = validate_variants(input_path, output_path)
                assert len(result_df) == 0
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    def test_validate_variants_missing_action_chain_column(self):
        """Test validation when action_chain column is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,variant_type\n")
            f.write("test_case_1,low\n")
            input_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name

            try:
                result_df = validate_variants(input_path, output_path)
                # Should mark all as valid when action_chain is missing
                assert len(result_df) == 1
                assert result_df.iloc[0]['is_valid'] is True
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

    def test_output_columns(self):
        """Test that output has correct columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("case_id,variant_type,action_chain\n")
            f.write("test_case_1,low,\"grab, lift\"\n")
            input_path = f.name

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                output_path = f.name

            try:
                result_df = validate_variants(input_path, output_path)

                # Check required columns
                assert 'case_id' in result_df.columns
                assert 'variant_type' in result_df.columns
                assert 'is_valid' in result_df.columns
            finally:
                if os.path.exists(output_path):
                    os.unlink(output_path)
        finally:
            if os.path.exists(input_path):
                os.unlink(input_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])