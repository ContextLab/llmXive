"""
Unit tests for the Pilot Human Manipulation Check (T019)

Tests verify:
1. Agreement calculation logic
2. Threshold-based flagging
3. Error handling for missing data
4. Output file generation
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.manipulation_check import (
    ManipulationCheckError,
    load_manipulated_scenarios,
    collect_coder_annotations,
    calculate_agreement,
    save_results,
    AGREEMENT_THRESHOLD,
    MIN_CODERS_REQUIRED
)


class TestLoadManipulatedScenarios(unittest.TestCase):
    """Tests for load_manipulated_scenarios function."""

    def setUp(self):
        """Set up temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.scenarios_file = Path(self.temp_dir) / "valid_scenarios.csv"
        self.variants_file = Path(self.temp_dir) / "stimulus_variants.csv"

        # Create mock valid_scenarios.csv
        scenarios_data = {
            "scenario_id": ["S001", "S002", "S003"],
            "image_path": ["img1.jpg", "img2.jpg", "img3.jpg"],
            "ambiguity_label": ["ambiguous", "ambiguous", "ambiguous"]
        }
        pd.DataFrame(scenarios_data).to_csv(self.scenarios_file, index=False)

        # Create mock stimulus_variants.csv with manipulated variants
        variants_data = {
            "variant_id": ["V001", "V002", "V003", "V004", "V005"],
            "scenario_id": ["S001", "S001", "S002", "S002", "S003"],
            "salience_level": ["low", "medium", "low", "high", "medium"],
            "image_path": ["v1.jpg", "v2.jpg", "v3.jpg", "v4.jpg", "v5.jpg"]
        }
        pd.DataFrame(variants_data).to_csv(self.variants_file, index=False)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_manipulated_scenarios_success(self):
        """Test successful loading of manipulated scenarios."""
        result = load_manipulated_scenarios(self.temp_dir)
        
        self.assertEqual(len(result), 5)  # All 5 variants are manipulated
        self.assertTrue(all(
            r["salience_level"] in ["low", "medium", "high"]
            for r in result
        ))

    def test_load_manipulated_scenarios_missing_file(self):
        """Test error when scenarios file is missing."""
        (self.scenarios_file).unlink()
        
        with self.assertRaises(ManipulationCheckError):
            load_manipulated_scenarios(self.temp_dir)

    def test_load_manipulated_scenarios_no_variants(self):
        """Test error when no manipulated variants exist."""
        # Create variants file with only 'original' salience level
        variants_data = {
            "variant_id": ["V001"],
            "scenario_id": ["S001"],
            "salience_level": ["original"],
            "image_path": ["v1.jpg"]
        }
        pd.DataFrame(variants_data).to_csv(self.variants_file, index=False)
        
        with self.assertRaises(ManipulationCheckError):
            load_manipulated_scenarios(self.temp_dir)


class TestCollectCoderAnnotations(unittest.TestCase):
    """Tests for collect_coder_annotations function."""

    def test_collect_annotations_file_exists(self):
        """Test loading annotations when file exists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("scenario_id,annotator_id,narrative_preserved\n")
            f.write("S001,A1,True\n")
            f.write("S001,A2,True\n")
            f.write("S001,A3,False\n")
            temp_path = f.name

        try:
            result = collect_coder_annotations([], temp_path)
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]["scenario_id"], "S001")
        finally:
            os.unlink(temp_path)

    def test_collect_annotations_file_missing(self):
        """Test error when annotations file is missing."""
        with self.assertRaises(ManipulationCheckError):
            collect_coder_annotations([], "nonexistent_file.csv")


class TestCalculateAgreement(unittest.TestCase):
    """Tests for calculate_agreement function."""

    def test_perfect_agreement(self):
        """Test calculation with perfect agreement."""
        annotations = [
            {"scenario_id": "S001", "annotator_id": "A1", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A2", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A3", "narrative_preserved": True},
        ]
        scenarios = [{"scenario_id": "S001", "salience_level": "low"}]
        
        rates, flags = calculate_agreement(annotations, scenarios)
        
        self.assertEqual(rates["S001"], 1.0)
        self.assertEqual(flags["S001"], "pass")

    def test_below_threshold(self):
        """Test calculation when agreement is below threshold."""
        annotations = [
            {"scenario_id": "S001", "annotator_id": "A1", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A2", "narrative_preserved": False},
            {"scenario_id": "S001", "annotator_id": "A3", "narrative_preserved": False},
        ]
        scenarios = [{"scenario_id": "S001", "salience_level": "low"}]
        
        rates, flags = calculate_agreement(annotations, scenarios)
        
        self.assertEqual(rates["S001"], 1/3)  # ~0.33
        self.assertEqual(flags["S001"], "fail")

    def test_insufficient_coders(self):
        """Test handling of insufficient coders."""
        annotations = [
            {"scenario_id": "S001", "annotator_id": "A1", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A2", "narrative_preserved": True},
        ]
        scenarios = [{"scenario_id": "S001", "salience_level": "low"}]
        
        rates, flags = calculate_agreement(annotations, scenarios)
        
        self.assertEqual(rates["S001"], 0.0)
        self.assertEqual(flags["S001"], "fail_insufficient_data")

    def test_multiple_scenarios(self):
        """Test calculation with multiple scenarios."""
        annotations = [
            {"scenario_id": "S001", "annotator_id": "A1", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A2", "narrative_preserved": True},
            {"scenario_id": "S001", "annotator_id": "A3", "narrative_preserved": True},
            {"scenario_id": "S002", "annotator_id": "A1", "narrative_preserved": True},
            {"scenario_id": "S002", "annotator_id": "A2", "narrative_preserved": False},
            {"scenario_id": "S002", "annotator_id": "A3", "narrative_preserved": False},
        ]
        scenarios = [
            {"scenario_id": "S001", "salience_level": "low"},
            {"scenario_id": "S002", "salience_level": "medium"}
        ]
        
        rates, flags = calculate_agreement(annotations, scenarios)
        
        self.assertEqual(rates["S001"], 1.0)
        self.assertEqual(flags["S001"], "pass")
        self.assertEqual(rates["S002"], 1/3)
        self.assertEqual(flags["S002"], "fail")


class TestSaveResults(unittest.TestCase):
    """Tests for save_results function."""

    def test_save_results_creates_file(self):
        """Test that save_results creates the output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "results.csv"
            
            scenarios = [
                {"scenario_id": "S001", "salience_level": "low"},
                {"scenario_id": "S002", "salience_level": "medium"}
            ]
            agreement_rates = {"S001": 1.0, "S002": 0.33}
            flags = {"S001": "pass", "S002": "fail"}
            
            save_results(scenarios, agreement_rates, flags, str(output_path))
            
            self.assertTrue(output_path.exists())
            
            # Verify content
            df = pd.read_csv(output_path)
            self.assertEqual(len(df), 2)
            self.assertEqual(df["scenario_id"].tolist(), ["S001", "S002"])
            self.assertEqual(df["status"].tolist(), ["pass", "fail"])


if __name__ == "__main__":
    unittest.main()
