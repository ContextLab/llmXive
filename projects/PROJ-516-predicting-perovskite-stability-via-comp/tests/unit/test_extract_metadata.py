import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path for imports
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from extract_metadata import (
    parse_source_metadata,
    process_metadata_entries,
    validate_metadata_structure,
    generate_uncertainty_flags
)

class TestExtractMetadata:
    def test_parse_source_metadata_valid_json(self):
        """Test parsing valid source metadata JSON."""
        data = [
            {
                "formula": "CsPbI3",
                "source": "NREL",
                "source_metadata": '{"tga_model": "TGA550", "temperature_precision": 0.5}'
            },
            {
                "formula": "MAPbI3",
                "source": "MP",
                "source_metadata": '{"instrument": "Mettler Toledo", "temperature_precision": "1.0"}'
            }
        ]
        df = pd.DataFrame(data)
        entries = parse_source_metadata(df)
        
        assert len(entries) == 2
        assert entries[0]["tga_model"] == "TGA550"
        assert entries[0]["temperature_precision"] == 0.5
        assert entries[1]["tga_model"] == "Mettler Toledo"
        assert entries[1]["temperature_precision"] == 1.0

    def test_parse_source_metadata_missing_column(self):
        """Test that missing source_metadata column raises KeyError."""
        data = [
            {"formula": "CsPbI3", "source": "NREL"}
        ]
        df = pd.DataFrame(data)
        with pytest.raises(KeyError):
            parse_source_metadata(df)

    def test_process_metadata_entries_uncertainty_calculation(self):
        """Test that combined uncertainty is calculated correctly."""
        entries = [
            {
                "formula": "CsPbI3",
                "source": "NREL",
                "tga_model": "TGA550",
                "temperature_precision": 0.5,
                "precision_source": "explicit",
                "raw_metadata": {"experimental_error": 0.2}
            }
        ]
        
        structured_meta, flags = process_metadata_entries(entries)
        
        assert len(structured_meta) == 1
        # sigma = sqrt(precision^2 + error^2) = sqrt(0.25 + 0.04) = sqrt(0.29) ≈ 0.5385
        expected_sigma = (0.5**2 + 0.2**2)**0.5
        assert abs(structured_meta[0]["combined_sigma"] - expected_sigma) < 1e-4
        assert flags[0]["weight"] == pytest.approx(1.0 / (expected_sigma**2))

    def test_validate_metadata_structure(self):
        """Test validation of metadata structure."""
        valid_meta = [
            {
                "formula": "CsPbI3",
                "tga_model": "TGA550",
                "temperature_precision": 0.5,
                "combined_sigma": 0.5
            }
        ]
        assert validate_metadata_structure(valid_meta) is True

        invalid_meta = [
            {
                "formula": "CsPbI3",
                # Missing required keys
                "tga_model": "TGA550"
            }
        ]
        assert validate_metadata_structure(invalid_meta) is False

    def test_generate_uncertainty_flags(self):
        """Test generation of uncertainty flags."""
        meta = [
            {
                "formula": "CsPbI3",
                "combined_sigma": 0.5,
                "precision_source": "explicit"
            }
        ]
        
        flags = generate_uncertainty_flags(meta)
        
        assert len(flags) == 1
        assert flags[0]["formula"] == "CsPbI3"
        assert flags[0]["sigma"] == 0.5
        assert flags[0]["weight"] == 4.0
        assert flags[0]["precision_source"] == "explicit"

    def test_end_to_end_json_write(self):
        """Test that the main functions produce valid JSON output."""
        data = [
            {
                "formula": "CsPbI3",
                "source": "NREL",
                "source_metadata": '{"tga_model": "TGA550", "temperature_precision": 0.5}'
            }
        ]
        df = pd.DataFrame(data)
        
        entries = parse_source_metadata(df)
        structured_meta, flags = process_metadata_entries(entries)
        
        # Serialize to check validity
        meta_json = json.dumps(structured_meta)
        flags_json = json.dumps(flags)
        
        assert json.loads(meta_json) is not None
        assert json.loads(flags_json) is not None
        assert len(json.loads(meta_json)) == 1
        assert len(json.loads(flags_json)) == 1
