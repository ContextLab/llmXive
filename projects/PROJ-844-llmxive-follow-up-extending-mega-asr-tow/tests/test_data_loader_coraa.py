import pytest
import os
import sys
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_loader import (
    compute_file_hash,
    verify_checksum,
    fetch_and_verify_coraa_mupe_asr,
    load_coraa_mupe_asr_subset,
    stratified_sample,
    save_stratified_subset
)

class TestCORAADataLoader:
    @pytest.fixture
    def temp_dir(self, tmp_path):
        return tmp_path / "coraa_test"

    def test_compute_file_hash(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        hash_val = compute_file_hash(test_file)
        assert len(hash_val) == 64 # SHA256 hex length
        assert isinstance(hash_val, str)

    def test_verify_checksum_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        # Compute hash
        correct_hash = compute_file_hash(test_file)
        assert verify_checksum(test_file, correct_hash) is True

    def test_verify_checksum_failure(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        wrong_hash = "a" * 64
        assert verify_checksum(test_file, wrong_hash) is False

    def test_verify_checksum_file_not_found(self, tmp_path):
        missing_file = tmp_path / "missing.txt"
        with pytest.raises(FileNotFoundError):
            verify_checksum(missing_file, "somehash")

    @patch('data_loader.load_dataset')
    def test_fetch_and_verify_coraa_mupe_asr_success(self, mock_load_dataset, temp_dir):
        # Mock the dataset loading
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        
        # Call function
        result = fetch_and_verify_coraa_mupe_asr(temp_dir)
        
        # Verify load_dataset was called
        mock_load_dataset.assert_called_once()
        assert len(result) > 0

    @patch('data_loader.load_dataset')
    def test_fetch_and_verify_coraa_mupe_asr_failure(self, mock_load_dataset, temp_dir):
        mock_load_dataset.side_effect = Exception("Dataset not found")
        
        with pytest.raises(RuntimeError, match="Failed to fetch CORAA-MUPE-ASR"):
            fetch_and_verify_coraa_mupe_asr(temp_dir)

    def test_stratified_sample(self):
        # Create dummy data
        data = [
            {"speaker_id": "A", "snr_bucket": "low", "text": "1"},
            {"speaker_id": "A", "snr_bucket": "low", "text": "2"},
            {"speaker_id": "A", "snr_bucket": "high", "text": "3"},
            {"speaker_id": "B", "snr_bucket": "low", "text": "4"},
            {"speaker_id": "B", "snr_bucket": "high", "text": "5"},
            {"speaker_id": "B", "snr_bucket": "high", "text": "6"},
        ]
        
        sample = stratified_sample(data, 3, ["speaker_id", "snr_bucket"])
        assert len(sample) == 3
        # Check that sampling is balanced (approx)
        speakers = [s["speaker_id"] for s in sample]
        assert "A" in speakers
        assert "B" in speakers

    def test_save_stratified_subset(self, tmp_path):
        data = [{"text": "test1"}, {"text": "test2"}]
        output_path = tmp_path / "output.jsonl"
        save_stratified_subset(data, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["text"] == "test1"

    def test_load_coraa_mupe_asr_subset_failure(self):
        with patch('data_loader.load_dataset', side_effect=Exception("Not found")):
            with pytest.raises(RuntimeError):
                load_coraa_mupe_asr_subset()
