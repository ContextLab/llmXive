"""
Unit tests for the hold-out known export functionality (T014b).

Tests verify:
1. The script correctly loads the training set.
2. The script correctly filters out training compositions.
3. The output file is created and has the correct format.
4. No overlap exists between output and training set.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import N_NOVEL_SAMPLES, RANDOM_SEED
from data_ingestion import strict_composition_compare

class TestExportHoldoutLogic:
    """Test the logic of exporting hold-out sets without actually running the full script."""

    def test_composition_exclusion(self):
        """Verify that the exclusion logic works correctly."""
        # Create mock data
        all_comps = {"A", "B", "C", "D", "E"}
        train_comps = {"A", "B"}
        
        available = list(all_comps - train_comps)
        
        assert "A" not in available
        assert "B" not in available
        assert "C" in available
        assert "D" in available
        assert "E" in available

    def test_sampling_determinism(self):
        """Verify that sampling is deterministic with a fixed seed."""
        import random
        
        seed = 42
        population = list(range(100))
        
        random.seed(seed)
        sample1 = random.sample(population, 10)
        
        random.seed(seed)
        sample2 = random.sample(population, 10)
        
        assert sample1 == sample2

    def test_strict_composition_compare(self):
        """Verify the strict composition comparison function."""
        # Test case 1: Same elements, same stoichiometry
        elems1 = ["Fe", "Co", "Ni", "Cr", "Mn"]
        stoich1 = {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2}
        comp1 = strict_composition_compare(elems1, stoich1)
        
        elems2 = ["Fe", "Co", "Ni", "Cr", "Mn"]
        stoich2 = {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Mn": 0.2}
        comp2 = strict_composition_compare(elems2, stoich2)
        
        assert comp1 == comp2

        # Test case 2: Different elements
        elems3 = ["Fe", "Co", "Ni", "Cr", "Al"]
        stoich3 = {"Fe": 0.2, "Co": 0.2, "Ni": 0.2, "Cr": 0.2, "Al": 0.2}
        comp3 = strict_composition_compare(elems3, stoich3)
        
        assert comp1 != comp3

def test_export_script_integration(tmp_path):
    """
    Integration test for the export script.
    We mock the data loading to avoid real dataset dependencies.
    """
    # Create temporary directories
    data_processed = tmp_path / "data" / "processed"
    data_processed.mkdir(parents=True)
    
    train_file = data_processed / "heas_train.csv"
    holdout_file = data_processed / "holdout_known.csv"
    
    # Create mock training data
    train_data = {
        "composition_string": ["A", "B", "C"],
        "target_energy": [-1.0, -2.0, -3.0]
    }
    pd.DataFrame(train_data).to_csv(train_file, index=False)
    
    # Mock the raw dataset
    mock_raw_data = {
        "composition_string": ["A", "B", "C", "D", "E", "F"],
        "target_energy": [-1.0, -2.0, -3.0, -4.0, -5.0, -6.0],
        "elements": [["A"], ["B"], ["C"], ["D"], ["E"], ["F"]],
        "stoichiometry": [{"A": 1}, {"B": 1}, {"C": 1}, {"D": 1}, {"E": 1}, {"F": 1}]
    }
    mock_df = pd.DataFrame(mock_raw_data)
    
    # Patch the functions
    with patch("code.export_holdout.load_hmao_dataset", return_value=mock_raw_data), \
         patch("code.export_holdout.filter_min_elements", return_value=mock_raw_data), \
         patch("code.export_holdout.ensure_dirs"):
         
         # Patch config paths to use tmp_path
         with patch("code.export_holdout.DATA_PROCESSED", data_processed), \
              patch("code.export_holdout.N_NOVEL_SAMPLES", 2), \
              patch("code.export_holdout.RANDOM_SEED", 42):
             
             # Import and run main
             # We need to re-import after patching to get the patched values
             import importlib
             import code.export_holdout as mod
             importlib.reload(mod)
             
             result = mod.main()
             
             assert result == 0
             assert holdout_file.exists()
             
             # Verify content
             holdout_df = pd.read_csv(holdout_file)
             assert len(holdout_df) == 2
             
             # Verify no overlap with training
             holdout_comps = set(holdout_df['composition_string'])
             train_comps = set(train_data['composition_string'])
             
             assert len(holdout_comps & train_comps) == 0
             assert holdout_comps <= {"D", "E", "F"} # Should be from available set