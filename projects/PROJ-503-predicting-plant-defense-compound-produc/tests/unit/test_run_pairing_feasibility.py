import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.run_pairing_feasibility import (
    load_json_safe,
    extract_geo_biosample_ids,
    extract_mw_biosample_ids,
    run_pairing_feasibility
)
from code.exceptions import E_PAIRING

class TestRunPairingFeasibility:
    
    def test_load_json_safe_missing_file(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        result = load_json_safe(non_existent)
        assert result == {}

    def test_load_json_safe_invalid_json(self, tmp_path):
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        result = load_json_safe(invalid_file)
        assert result == {}

    def test_extract_geo_biosample_ids(self):
        geo_data = {
            "arabidopsis": {
                "results": [
                    {
                        "accession": "GSE123",
                        "samples": [
                            {"biosample_id": "SAM001"},
                            {"biosample_id": "SAM002"}
                        ]
                    }
                ]
            }
        }
        ids = extract_geo_biosample_ids(geo_data)
        assert ids == {"SAM001", "SAM002"}

    def test_extract_mw_biosample_ids(self):
        mw_data = {
            "experiments": [
                {
                    "id": "STUDY001",
                    "samples": [
                        {"biosample_id": "SAM001"},
                        {"biosample_id": "SAM003"}
                    ]
                }
            ]
        }
        ids = extract_mw_biosample_ids(mw_data)
        assert ids == {"SAM001", "SAM003"}

    def test_run_pairing_feasibility_high_rate(self, tmp_path):
        # Setup mock data files
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # GEO data with 10 samples
        geo_data = {
            "arabidopsis": {
                "results": [
                    {
                        "accession": "GSE123",
                        "samples": [{"biosample_id": f"SAM{i}"} for i in range(10)]
                    }
                ]
            }
        }
        with open(data_raw_dir / "geo_arabidopsis_search.json", 'w') as f:
            json.dump(geo_data, f)
        
        # MW data with 10 samples, 9 matching
        mw_data = {
            "experiments": [
                {
                    "id": "STUDY001",
                    "samples": [{"biosample_id": f"SAM{i}"} for i in range(9)] + [{"biosample_id": "SAM99"}]
                }
            ]
        }
        with open(data_raw_dir / "metabolomics_workbench_search.json", 'w') as f:
            json.dump(mw_data, f)
        
        # Run analysis
        result = run_pairing_feasibility(tmp_path)
        
        # Total unique: SAM0-SAM9 (10) + SAM99 (1) = 11
        # Matched: SAM0-SAM8 (9)
        # Rate: 9/11 = 0.818... which is < 0.95
        # Let's adjust: 10 geo, 10 mw, 10 match -> rate 10/10 = 1.0
        
        mw_data_high = {
            "experiments": [
                {
                    "id": "STUDY001",
                    "samples": [{"biosample_id": f"SAM{i}"} for i in range(10)]
                }
            ]
        }
        with open(data_raw_dir / "metabolomics_workbench_search.json", 'w') as f:
            json.dump(mw_data_high, f)
        
        result = run_pairing_feasibility(tmp_path)
        
        assert result["pairing_rate"] == 1.0
        assert result["matched_samples"] == 10
        assert result["total_samples"] == 10
        assert result["status"] == "OK"

    def test_run_pairing_feasibility_low_rate_raises(self, tmp_path):
        # Setup mock data files
        data_raw_dir = tmp_path / "data" / "raw"
        data_raw_dir.mkdir(parents=True)
        
        # GEO: 100 samples
        geo_data = {
            "arabidopsis": {
                "results": [
                    {
                        "accession": "GSE123",
                        "samples": [{"biosample_id": f"SAM{i}"} for i in range(100)]
                    }
                ]
            }
        }
        with open(data_raw_dir / "geo_arabidopsis_search.json", 'w') as f:
            json.dump(geo_data, f)
        
        # MW: 10 samples, all matching (10% rate)
        mw_data = {
            "experiments": [
                {
                    "id": "STUDY001",
                    "samples": [{"biosample_id": f"SAM{i}"} for i in range(10)]
                }
            ]
        }
        with open(data_raw_dir / "metabolomics_workbench_search.json", 'w') as f:
            json.dump(mw_data, f)
        
        # This should raise E_PAIRING because rate < 0.95
        with pytest.raises(E_PAIRING):
            run_pairing_feasibility(tmp_path)