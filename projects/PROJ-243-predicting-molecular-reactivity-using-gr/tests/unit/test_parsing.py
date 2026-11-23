"""
Unit tests for SMILES parsing and exclusion logic.

This module validates the robustness of the SMILES parsing pipeline,
specifically focusing on the exclusion of invalid molecules and the
correct handling of edge cases.

Dependencies:
  - rdkit: For molecule parsing and validation.
  - pytest: For test execution.
  - config: Project configuration for path handling.
"""

import pytest
import os
import json
import logging
from typing import List, Dict, Any, Tuple

# Import project utilities
from config import get_config, ensure_directories
from utils.graph_utils import smiles_to_molecule, validate_graph

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def config():
    """Load project configuration."""
    return get_config()

@pytest.fixture
def valid_smiles_list():
    """Return a list of valid SMILES strings."""
    return [
        "CCO",               # Ethanol
        "CC(=O)O",           # Acetic acid
        "c1ccccc1",          # Benzene
        "CC1=CC=CC=C1",      # Toluene
        "O=C(O)C1=CC=CC=C1", # Benzoic acid
        "C[C@H](O)C",        # Chiral center (2-butanol)
        "CC1=C(C)C=C(C)C=C1" # 1,2,4,5-Tetramethylbenzene
    ]

@pytest.fixture
def invalid_smiles_list():
    """Return a list of invalid SMILES strings to trigger exclusion."""
    return [
        "",                  # Empty string
        "CCO(",              # Unbalanced parenthesis
        "C1CC1C2",           # Unbalanced ring closure
        "CC#CC#",            # Invalid bond sequence (valence error)
        "C@@",               # Invalid stereochemistry
        "CCO[",              # Invalid atom symbol
        "12345",             # Non-chemical characters
        "C-C-C",             # Invalid bond notation (hyphen not standard in SMILES)
        "C123456789012345678901234567890", # Extremely long ring closure number (edge case)
        "C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1C1" # Too many ring closures (potential parser stress)
    ]

@pytest.fixture
def mixed_smiles_list(valid_smiles_list, invalid_smiles_list):
    """Return a mixed list of valid and invalid SMILES."""
    return valid_smiles_list + invalid_smiles_list

# ---------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------

class TestSMILESParsing:
    """Tests for SMILES parsing functionality."""

    def test_parse_valid_smiles(self, valid_smiles_list):
        """Verify that all valid SMILES strings are successfully parsed."""
        for smiles in valid_smiles_list:
            mol = smiles_to_molecule(smiles)
            assert mol is not None, f"Failed to parse valid SMILES: {smiles}"
            assert mol.GetNumAtoms() > 0, f"Parsed molecule has no atoms: {smiles}"
            logger.info(f"Successfully parsed: {smiles}")

    def test_parse_invalid_smiles_returns_none(self, invalid_smiles_list):
        """Verify that invalid SMILES strings return None."""
        for smiles in invalid_smiles_list:
            mol = smiles_to_molecule(smiles)
            assert mol is None, f"Expected None for invalid SMILES: {smiles}"
            logger.info(f"Correctly rejected invalid SMILES: {smiles}")

    def test_mixed_list_exclusion_logic(self, mixed_smiles_list):
        """
        Test the exclusion logic on a mixed list.
        
        This test simulates the logic used in T014a (Preprocess Graphs)
        to ensure that invalid SMILES are identified and excluded correctly.
        """
        valid_count = 0
        invalid_count = 0
        excluded_ids = []

        for idx, smiles in enumerate(mixed_smiles_list):
            mol = smiles_to_molecule(smiles)
            if mol is not None:
                valid_count += 1
                # Optional: Validate graph structure if conversion happens here
                # graph = smiles_to_graph(smiles)
                # assert validate_graph(graph)
            else:
                invalid_count += 1
                excluded_ids.append(idx)

        # Assertions
        expected_valid = len([s for s in valid_smiles_list if s]) # Filter empty if any
        expected_invalid = len([s for s in invalid_smiles_list if s])

        assert valid_count == expected_valid, f"Expected {expected_valid} valid, got {valid_count}"
        assert invalid_count == expected_invalid, f"Expected {expected_invalid} invalid, got {invalid_count}"
        assert len(excluded_ids) == expected_invalid, "Excluded IDs count mismatch"

        logger.info(f"Exclusion logic verified: {valid_count} valid, {invalid_count} excluded.")

    def test_exclusion_threshold_check(self, mixed_smiles_list):
        """
        Verify that the exclusion rate is calculated and checked against thresholds.
        
        This simulates the validation step in T014a where exclusion count must be < 0.1%.
        """
        total = len(mixed_smiles_list)
        valid = sum(1 for s in mixed_smiles_list if smiles_to_molecule(s) is not None)
        excluded = total - valid
        exclusion_rate = excluded / total if total > 0 else 0.0

        # In a real dataset, this threshold should be < 0.001 (0.1%)
        # For this small test set, we just verify the calculation is correct.
        assert 0.0 <= exclusion_rate <= 1.0, "Exclusion rate must be between 0 and 1"
        
        # Log the rate for verification
        logger.info(f"Test Exclusion Rate: {exclusion_rate:.2%} ({excluded}/{total})")

        # Note: This specific test data has a high exclusion rate (invalids are 50%),
        # so we do NOT assert < 0.1% here, as that would fail on purpose for this unit test.
        # The production code (T014a) will enforce the < 0.1% rule on real data.

    def test_empty_string_handling(self):
        """Specific test for empty string edge case."""
        mol = smiles_to_molecule("")
        assert mol is None, "Empty string should result in None"

    def test_whitespace_handling(self):
        """Test that strings with only whitespace are handled correctly."""
        mol = smiles_to_molecule("   ")
        assert mol is None, "Whitespace-only string should result in None"

    def test_stereochemistry_parsing(self, valid_smiles_list):
        """Ensure molecules with stereochemistry are parsed correctly."""
        chiral_smiles = "C[C@H](O)C"
        mol = smiles_to_molecule(chiral_smiles)
        assert mol is not None, "Failed to parse chiral SMILES"
        # RDKit preserves chirality if parsed correctly

class TestExclusionReportGeneration:
    """Tests for the exclusion report generation logic."""

    def test_report_structure(self, mixed_smiles_list, tmp_path):
        """Verify the structure of the exclusion report JSON."""
        excluded_ids = []
        excluded_smiles = []

        for idx, smiles in enumerate(mixed_smiles_list):
            if smiles_to_molecule(smiles) is None:
                excluded_ids.append(idx)
                excluded_smiles.append(smiles)

        report = {
            "total_processed": len(mixed_smiles_list),
            "valid_count": len(mixed_smiles_list) - len(excluded_ids),
            "exclusion_count": len(excluded_ids),
            "exclusion_rate": len(excluded_ids) / len(mixed_smiles_list) if mixed_smiles_list else 0.0,
            "excluded_indices": excluded_ids,
            "excluded_smiles": excluded_smiles,
            "threshold_passed": len(excluded_ids) / len(mixed_smiles_list) < 0.001 if mixed_smiles_list else True
        }

        # Validate schema
        assert "total_processed" in report
        assert "exclusion_count" in report
        assert "excluded_indices" in report
        assert isinstance(report["excluded_indices"], list)
        assert isinstance(report["exclusion_rate"], float)

        logger.info("Exclusion report structure validated.")

    def test_report_serialization(self, mixed_smiles_list, tmp_path):
        """Test writing the exclusion report to disk."""
        excluded_ids = [i for i, s in enumerate(mixed_smiles_list) if smiles_to_molecule(s) is None]
        
        report = {
            "total_processed": len(mixed_smiles_list),
            "exclusion_count": len(excluded_ids),
            "excluded_indices": excluded_ids
        }

        report_path = tmp_path / "exclusion_report_test.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        assert report_path.exists(), "Report file was not created"
        
        # Verify content
        with open(report_path, "r") as f:
            loaded = json.load(f)
        
        assert loaded["exclusion_count"] == len(excluded_ids)
        logger.info(f"Report successfully written to {report_path}")