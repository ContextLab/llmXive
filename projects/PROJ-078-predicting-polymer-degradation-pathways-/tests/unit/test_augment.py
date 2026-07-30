import pytest
import pandas as pd
import json
from pathlib import Path
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from augment import (
    check_augmentation_trigger,
    functional_group_preserving_edge_dropout,
    canonicalize_smiles,
    augment_record,
    load_pre_augmented_dataset,
    augment_dataset,
    compute_checksum,
    is_ester_bond
)

class TestAugmentationTrigger:
    """Tests for augmentation trigger checking functionality."""
    
    def test_trigger_not_found(self, tmp_path):
        """Test behavior when trigger file doesn't exist."""
        # Temporarily change the trigger file path
        original_trigger = Path("state/augmentation_trigger.json")
        
        # Create a temporary directory structure
        temp_state = tmp_path / "state"
        temp_state.mkdir()
        
        # Mock the trigger file path
        import augment
        augment.TRIGGER_FILE = temp_state / "augmentation_trigger.json"
        
        result = check_augmentation_trigger()
        assert result is None
        
        # Restore original
        augment.TRIGGER_FILE = original_trigger

    def test_invalid_trigger_format(self, tmp_path):
        """Test behavior with invalid trigger format."""
        temp_state = tmp_path / "state"
        temp_state.mkdir()
        trigger_file = temp_state / "augmentation_trigger.json"
        
        # Write invalid JSON
        with open(trigger_file, "w") as f:
            json.dump({"invalid": "format"}, f)
        
        import augment
        original_trigger = augment.TRIGGER_FILE
        augment.TRIGGER_FILE = trigger_file
        
        result = check_augmentation_trigger()
        assert result is None
        
        augment.TRIGGER_FILE = original_trigger

    def test_valid_trigger(self, tmp_path):
        """Test behavior with valid trigger."""
        temp_state = tmp_path / "state"
        temp_state.mkdir()
        trigger_file = temp_state / "augmentation_trigger.json"
        
        # Write valid trigger
        with open(trigger_file, "w") as f:
            json.dump({"n": 100, "action": "augment"}, f)
        
        import augment
        original_trigger = augment.TRIGGER_FILE
        augment.TRIGGER_FILE = trigger_file
        
        result = check_augmentation_trigger()
        assert result is not None
        assert result["n"] == 100
        assert result["action"] == "augment"
        
        augment.TRIGGER_FILE = original_trigger

class TestEdgeDropout:
    """Tests for functional-group-preserving edge dropout."""
    
    def test_ester_bond_detection(self):
        """Test that ester bonds are correctly detected."""
        assert is_ester_bond("C(=O)O") is True
        assert is_ester_bond("C(=O)OC") is True
        assert is_ester_bond("COC(=O)") is True
        assert is_ester_bond("OC(=O)") is True
        assert is_ester_bond("CCCC") is False
        assert is_ester_bond("CCO") is False

    def test_edge_dropout_preserves_ester(self):
        """Test that edge dropout preserves ester bonds."""
        smiles = "CC(=O)OCCC"
        augmented = functional_group_preserving_edge_dropout(smiles, dropout_rate=0.5)
        
        # The ester bond should be preserved
        assert "C(=O)O" in augmented or "C(=O)OC" in augmented

    def test_edge_dropout_reduces_length(self):
        """Test that edge dropout can reduce SMILES length."""
        smiles = "CCCCCC"  # Non-ester chain
        augmented = functional_group_preserving_edge_dropout(smiles, dropout_rate=0.8)
        
        # Should be shorter but not empty
        assert len(augmented) < len(smiles)
        assert len(augmented) > 0

    def test_invalid_smiles_input(self):
        """Test handling of invalid SMILES input."""
        with pytest.raises(ValueError):
            functional_group_preserving_edge_dropout(None)
        
        with pytest.raises(ValueError):
            functional_group_preserving_edge_dropout("")

class TestCanonicalization:
    """Tests for SMILES canonicalization."""
    
    def test_canonicalize_basic(self):
        """Test basic canonicalization."""
        smiles = "ccccc"
        canonical = canonicalize_smiles(smiles)
        assert canonical == "CCCCC"

    def test_canonicalize_with_spaces(self):
        """Test canonicalization with spaces."""
        smiles = "  ccccc  "
        canonical = canonicalize_smiles(smiles)
        assert canonical == "CCCCC"

    def test_invalid_input(self):
        """Test handling of invalid input."""
        with pytest.raises(ValueError):
            canonicalize_smiles(None)
        
        with pytest.raises(ValueError):
            canonicalize_smiles("")

class TestRecordAugmentation:
    """Tests for single record augmentation."""
    
    def test_augment_record_basic(self):
        """Test basic record augmentation."""
        record = {
            "smiles": "CC(=O)OCCC",
            "degradation_pathway": "hydrolysis",
            "temperature": 25.0
        }
        
        augmented = augment_record(record)
        
        assert augmented["smiles"] != record["smiles"]  # Should be modified
        assert augmented["is_augmented"] is True
        assert augmented["original_smiles"] == record["smiles"]
        assert augmented["degradation_pathway"] == record["degradation_pathway"]

    def test_augment_record_invalid(self):
        """Test handling of invalid record."""
        with pytest.raises(ValueError):
            augment_record({})
        
        with pytest.raises(ValueError):
            augment_record({"smiles": None})

class TestDatasetAugmentation:
    """Tests for dataset-level augmentation."""
    
    def test_augment_dataset(self, tmp_path):
        """Test dataset augmentation."""
        # Create test data
        test_data = {
            "smiles": ["CC(=O)OCCC", "CCCCC", "COC(=O)CC"],
            "degradation_pathway": ["hydrolysis", "oxidation", "hydrolysis"],
            "temperature": [25.0, 30.0, 28.0]
        }
        df = pd.DataFrame(test_data)
        
        # Save to temp file
        temp_file = tmp_path / "test_pre_augmented.csv"
        df.to_csv(temp_file, index=False)
        
        # Mock the file path
        import augment
        original_file = augment.PRE_AUGMENTED_FILE
        augment.PRE_AUGMENTED_FILE = temp_file
        
        try:
            augmented_df = augment_dataset(df)
            
            # Should have same or more records
            assert len(augmented_df) >= len(df)
            assert "is_augmented" in augmented_df.columns
        finally:
            augment.PRE_AUGMENTED_FILE = original_file

class TestChecksum:
    """Tests for checksum computation."""
    
    def test_checksum_computation(self, tmp_path):
        """Test checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum1 = compute_checksum(test_file)
        checksum2 = compute_checksum(test_file)
        
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA256 hex length

    def test_different_content_different_checksum(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        checksum1 = compute_checksum(file1)
        checksum2 = compute_checksum(file2)
        
        assert checksum1 != checksum2

class TestIntegration:
    """Integration tests for the augmentation pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test the full augmentation pipeline."""
        # Create test data
        test_data = {
            "smiles": ["CC(=O)OCCC", "CCCCC", "COC(=O)CC"],
            "degradation_pathway": ["hydrolysis", "oxidation", "hydrolysis"],
            "temperature": [25.0, 30.0, 28.0]
        }
        df = pd.DataFrame(test_data)
        
        # Setup directory structure
        state_dir = tmp_path / "state"
        processed_dir = tmp_path / "data" / "processed"
        state_dir.mkdir()
        processed_dir.mkdir(parents=True)
        
        # Create trigger file
        trigger_file = state_dir / "augmentation_trigger.json"
        with open(trigger_file, "w") as f:
            json.dump({"n": 100, "action": "augment"}, f)
        
        # Create pre-augmented file
        pre_aug_file = processed_dir / "pre_augmented_graph_dataset.csv"
        df.to_csv(pre_aug_file, index=False)
        
        # Mock paths
        import augment
        original_trigger = augment.TRIGGER_FILE
        original_pre_aug = augment.PRE_AUGMENTED_FILE
        original_output = augment.OUTPUT_FILE
        original_log = augment.LOG_FILE
        
        augment.TRIGGER_FILE = trigger_file
        augment.PRE_AUGMENTED_FILE = pre_aug_file
        augment.OUTPUT_FILE = processed_dir / "augmented_graph_dataset.csv"
        augment.LOG_FILE = processed_dir / "augmentation_log.json"
        
        try:
            # Run augmentation
            augment.main()
            
            # Verify output
            assert augment.OUTPUT_FILE.exists()
            assert augment.LOG_FILE.exists()
            
            # Check output file
            output_df = pd.read_csv(augment.OUTPUT_FILE)
            assert len(output_df) >= len(df)
            assert "is_augmented" in output_df.columns
            
            # Check log file
            with open(augment.LOG_FILE, "r") as f:
                log_data = json.load(f)
            assert log_data["status"] == "completed"
        finally:
            augment.TRIGGER_FILE = original_trigger
            augment.PRE_AUGMENTED_FILE = original_pre_aug
            augment.OUTPUT_FILE = original_output
            augment.LOG_FILE = original_log