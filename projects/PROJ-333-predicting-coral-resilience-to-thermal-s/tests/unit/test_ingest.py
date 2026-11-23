import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from ingest import (
    map_treatment_condition,
    parse_and_filter_phenotypes,
    load_phenotype_metadata,
    IngestionError,
    TreatmentType
)
from utils.errors import ChecksumMismatchError

@pytest.fixture
def temp_metadata_dir():
    """Create a temporary directory with mock metadata and checksum files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create data directories
        data_raw = Path(tmpdir) / "data" / "raw"
        data_processed = Path(tmpdir) / "data" / "processed"
        data_raw.mkdir(parents=True, exist_ok=True)
        data_processed.mkdir(parents=True, exist_ok=True)

        # Create mock metadata CSV
        metadata_file = data_raw / "phenotype_metadata.csv"
        with open(metadata_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_id', 'treatment', 'condition'])
            writer.writerow(['SRR_001', 'heat', 'thermal'])
            writer.writerow(['SRR_002', 'control', 'ambient'])
            writer.writerow(['SRR_003', '', 'unknown'])  # Missing treatment
            writer.writerow(['SRR_004', 'invalid_val', 'bad']) # Invalid treatment
            writer.writerow(['SRR_005', 'Heat', 'high_temp']) # Valid variation
        
        # Create mock checksums JSON
        checksum_file = data_raw / "checksums.json"
        checksums = {
            "SRR_001": {"sha256": "abc", "verified": True},
            "SRR_002": {"sha256": "def", "verified": True},
            "SRR_003": {"sha256": "ghi", "verified": True},
            "SRR_004": {"sha256": "jkl", "verified": True},
            "SRR_005": {"sha256": "mno", "verified": True},
            "SRR_006": {"sha256": "pqr", "verified": True} # Not in metadata
        }
        with open(checksum_file, 'w') as f:
            json.dump(checksums, f)

        yield tmpdir

def test_map_treatment_condition_valid():
    """Test mapping of valid treatment strings."""
    assert map_treatment_condition("heat") == TreatmentType.HEAT
    assert map_treatment_condition("HEAT") == TreatmentType.HEAT
    assert map_treatment_condition("Heat") == TreatmentType.HEAT
    assert map_treatment_condition("thermal_stress") == TreatmentType.HEAT
    
    assert map_treatment_condition("control") == TreatmentType.CONTROL
    assert map_treatment_condition("CTRL") == TreatmentType.CONTROL
    assert map_treatment_condition("ambient") == TreatmentType.CONTROL
    assert map_treatment_condition("baseline") == TreatmentType.CONTROL

def test_map_treatment_condition_invalid():
    """Test mapping of invalid or missing treatment strings."""
    assert map_treatment_condition("") is None
    assert map_treatment_condition(None) is None
    assert map_treatment_condition("unknown") is None
    assert map_treatment_condition("invalid_val") is None

def test_parse_and_filter_phenotypes(temp_metadata_dir):
    """Test that parse_and_filter_phenotypes correctly filters samples."""
    import ingest
    import config
    import utils.logging
    
    # Mock the config and logging to avoid side effects
    with patch.object(ingest, 'METADATA_FILE', str(Path(temp_metadata_dir) / "data" / "raw" / "phenotype_metadata.csv")), \
         patch.object(ingest, 'CHECKSUM_FILE', str(Path(temp_metadata_dir) / "data" / "raw" / "checksums.json")), \
         patch.object(ingest, 'FILTERED_METADATA_FILE', str(Path(temp_metadata_dir) / "data" / "processed" / "filtered.csv")), \
         patch.object(ingest, 'EXCLUSION_LOG_FILE', str(Path(temp_metadata_dir) / "data" / "processed" / "exclusion.json")), \
         patch.object(config, 'ensure_directories'), \
         patch.object(utils.logging, 'setup_logger') as mock_logger:
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        valid_records, stats = parse_and_filter_phenotypes(mock_logger_instance, 10, 3)
        
        # Verify logging calls
        assert mock_logger_instance.warning.call_count >= 2 # At least for missing and invalid
        
        # Check results
        # SRR_001 (heat) -> Valid
        # SRR_002 (control) -> Valid
        # SRR_003 (missing) -> Excluded
        # SRR_004 (invalid) -> Excluded
        # SRR_005 (Heat) -> Valid
        
        assert len(valid_records) == 3
        sample_ids = {r.sample_id for r in valid_records}
        assert "SRR_001" in sample_ids
        assert "SRR_002" in sample_ids
        assert "SRR_005" in sample_ids
        
        assert "SRR_003" not in sample_ids
        assert "SRR_004" not in sample_ids
        
        assert stats["total_excluded"] == 2
        assert stats["missing_treatment_count"] == 1
        assert stats["invalid_treatment_count"] == 1

def test_parse_and_filter_phenotypes_missing_metadata(temp_metadata_dir):
    """Test behavior when metadata file is missing."""
    import ingest
    import config
    import utils.logging
    
    with patch.object(ingest, 'METADATA_FILE', "/nonexistent/path.csv"), \
         patch.object(ingest, 'CHECKSUM_FILE', str(Path(temp_metadata_dir) / "data" / "raw" / "checksums.json")), \
         patch.object(config, 'ensure_directories'), \
         patch.object(utils.logging, 'setup_logger') as mock_logger:
        
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance
        
        with pytest.raises(IngestionError, match="Phenotype metadata file not found"):
            parse_and_filter_phenotypes(mock_logger_instance, 10, 3)