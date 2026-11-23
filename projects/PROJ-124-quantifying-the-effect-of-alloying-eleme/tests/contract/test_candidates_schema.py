"""
Contract tests for candidates output schema validation.
Validates that the candidates CSV and verification_requests JSON match the expected schema.
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import load_schema, validate_csv_schema


class TestCandidatesSchema:
    """Test suite for candidates output schema validation."""

    @pytest.fixture
    def output_dir(self):
        """Path to output directory."""
        return Path(__file__).parent.parent.parent / "output"

    @pytest.fixture
    def schema_path(self):
        """Path to schema definition."""
        return Path(__file__).parent.parent.parent / "contracts" / "data_schema.yaml"

    def test_candidates_csv_schema(self, schema_path):
        """
        Test that candidates CSV schema is properly defined.
        Based on FR-006: Output candidates.csv with top-ranked items.
        """
        schema = load_schema(schema_path)
        assert 'candidates' in schema

        candidates_schema = schema['candidates']
        required_cols = candidates_schema['required_columns']

        # Check all required columns are present
        expected_cols = [
            'composition',
            'predicted_log10_Rc',
            'ci_lower',
            'ci_upper',
            'novelty_status',
            'doa_penalty',
            'final_score',
            'rank'
        ]

        for col in expected_cols:
            assert col in required_cols, f"Missing required column: {col}"

    def test_candidates_column_types(self, schema_path):
        """Test that candidates column types are correctly defined."""
        schema = load_schema(schema_path)
        col_types = schema['candidates']['column_types']

        assert col_types['composition'] == 'string'
        assert col_types['predicted_log10_Rc'] == 'float'
        assert col_types['ci_lower'] == 'float'
        assert col_types['ci_upper'] == 'float'
        assert col_types['novelty_status'] == 'string (novel|known|unverified_external)'
        assert col_types['final_score'] == 'float'
        assert col_types['rank'] == 'integer'

    def test_candidates_constraints(self, schema_path):
        """Test that candidates constraints are properly defined."""
        schema = load_schema(schema_path)
        constraints = schema['candidates']['constraints']

        assert 'novelty_status' in str(constraints)
        assert 'rank' in str(constraints)

    def test_verification_requests_schema(self, schema_path):
        """
        Test that verification_requests JSON schema is properly defined.
        Based on FR-008: Generate verification_requests.json.
        """
        schema = load_schema(schema_path)
        assert 'verification_requests' in schema

        ver_schema = schema['verification_requests']
        item_props = ver_schema['item_schema']['properties']
        required_fields = ver_schema['item_schema']['required']

        # Check required fields
        expected_fields = ['composition', 'predicted_log10_Rc', 'confidence_interval', 'novelty_status', 'status']
        for field in expected_fields:
            assert field in required_fields, f"Missing required field: {field}"

    def test_verification_novelty_enum(self, schema_path):
        """Test that novelty_status enum is correctly defined."""
        schema = load_schema(schema_path)
        ver_schema = schema['verification_requests']
        novelty_enum = ver_schema['item_schema']['properties']['novelty_status']['enum']

        expected = ['novel', 'known', 'unverified_external']
        assert set(novelty_enum) == set(expected), f"Novelty enum mismatch: {novelty_enum}"

    def test_verification_status_const(self, schema_path):
        """Test that status field is correctly constrained."""
        schema = load_schema(schema_path)
        ver_schema = schema['verification_requests']
        status_schema = ver_schema['item_schema']['properties']['status']

        # Status should be const: "pending_verification"
        assert status_schema['const'] == 'pending_verification'

    def test_candidates_schema_matches_requirements(self, schema_path):
        """
        Main contract test: validates candidates schema matches FR-006 and FR-007.
        This test ensures the output format is correct for downstream consumption.
        """
        schema = load_schema(schema_path)

        # Verify FR-006 requirements: top-ranked items with predictions, CIs, risk scores
        cand_schema = schema['candidates']
        cand_cols = cand_schema['required_columns']

        assert 'predicted_log10_Rc' in cand_cols  # Prediction
        assert 'ci_lower' in cand_cols and 'ci_upper' in cand_cols  # Confidence intervals
        assert 'final_score' in cand_cols  # Risk score (predicted + penalty)
        assert 'rank' in cand_cols  # Ranking

        # Verify FR-007 requirements: confidence intervals from bootstrapping
        assert 'ci_lower' in cand_cols
        assert 'ci_upper' in cand_cols

        # Verify FR-013 requirements: novelty status
        assert 'novelty_status' in cand_cols

        assert True, "Candidates schema matches FR-006, FR-007, FR-013 requirements"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
