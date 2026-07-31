import json
import os
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion import run_ingestion_pipeline

class TestT018Integration:
    """Integration test for T018: End-to-end ingestion and audit generation."""

    @patch('ingestion.get_dataset_url', return_value="http://mock.com/data.csv")
    @patch('ingestion.requests.get')
    def test_end_to_end_artifact_creation(self, mock_get, mock_url, tmp_path):
        """
        Run the full pipeline and verify:
        1. cleaned_alloys.csv exists and has correct columns
        2. retention_audit.json exists and has correct stats
        3. Retention % >= 70% and count >= 200 (if mock data satisfies)
        """
        # Setup mock data: 300 rows, 250 metallic, 0 missing -> 250 final
        # 250/300 = 83.33% retention. 250 >= 200. Should PASS.
        mock_data = {
            'id': range(300),
            'material_type': ['metal'] * 250 + ['polymer'] * 50,
            'iron_wt': [50.0] * 300,
            'carbon_wt': [0.5] * 300,
            'degradation_mode': ['pitting'] * 100 + ['scc'] * 100 + ['uniform'] * 100
        }
        df_mock = pd.DataFrame(mock_data)
        csv_content = df_mock.to_csv(index=False)

        mock_response = MagicMock()
        mock_response.content = csv_content.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Setup temp directories
        raw_dir = tmp_path / "data" / "raw"
        proc_dir = tmp_path / "data" / "processed"
        raw_dir.mkdir(parents=True)
        proc_dir.mkdir(parents=True)

        raw_file = raw_dir / "corrosion_alloys_raw.csv"
        
        # Patch the paths in the ingestion module
        with patch('ingestion.PROCESSED_DIR', proc_dir), \
             patch('ingestion.Path', lambda x: Path(tmp_path) / x if not str(x).startswith('/') else Path(x)):
            
            # We need to patch the specific constants inside the module
            # Since we can't easily re-import, we patch the module's attributes
            import ingestion
            ingestion.PROCESSED_DIR = proc_dir
            ingestion.CLEANED_OUTPUT = proc_dir / "cleaned_alloys.csv"
            ingestion.RETENTION_AUDIT = proc_dir / "retention_audit.json"
            ingestion.RAW_DATA_FILENAME = "corrosion_alloys_raw.csv"

            # Run pipeline
            result = run_ingestion_pipeline()

            # Assertions
            assert result['status'] == "PASS", f"Expected PASS, got {result['status']}. Stats: {result}"
            assert result['final_count'] == 250
            assert abs(result['retention_percentage'] - 83.33) < 0.1

            # Check files exist
            assert proc_dir.exists()
            assert (proc_dir / "cleaned_alloys.csv").exists()
            assert (proc_dir / "retention_audit.json").exists()

            # Verify JSON content
            with open(proc_dir / "retention_audit.json") as f:
                audit = json.load(f)
            assert audit['final_count'] == 250
            assert audit['status'] == "PASS"

            # Verify CSV content
            df_out = pd.read_csv(proc_dir / "cleaned_alloys.csv")
            assert len(df_out) == 250
            assert 'material_type' in df_out.columns
            assert all(df_out['material_type'] == 'metal')

if __name__ == "__main__":
    pytest.main([__file__, "-v"])