"""
Integration test for the full download-and-align flow (User Story 1).

This test verifies the end-to-end pipeline:
1. Ingests real historical data from NOAA/CDAWeb (or mocked responses if network fails).
2. Aligns solar events with geomagnetic storms within a 3-day window.
3. Produces `data/processed/aligned_events.csv`.
4. Asserts the file exists and contains > 0 rows.

NOTE: This task explicitly requires a mocked FTP response with representative
schema-valid data to ensure the test is deterministic and runnable in CI/CD
environments without relying on live network stability for the *structure*
verification, while still validating the real ingestion logic paths.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO
import tempfile
import shutil

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from code.ingest import (
    fetch_goess_flare_list,
    fetch_cme_catalog,
    fetch_dst_indices_http,
    fetch_kp_indices_http,
    ensure_directories,
    load_manifest,
    save_manifest,
    update_manifest_entry
)
from code.align import align_events, flag_recurrent_activity
from code.validate import load_schema, validate_aligned_events
from code.write_aligned_output import write_aligned_events, compute_file_checksum
from code.filter_analysis_subset import filter_non_recurrent_storms

# Mock Data: Representative schema-valid synthetic data for deterministic testing
# These strings mimic the exact format returned by NOAA/CDAWeb APIs/FTP
MOCK_GOES_FLARE_CSV = """event_date,start_time,peak_time,end_time,flux,source,region
2015-01-01,00:05,00:10,00:15,1.2e-05,M1.0,12345
2015-01-02,12:00,12:05,12:10,5.0e-06,C5.0,12346
2015-01-05,08:30,08:35,08:40,2.0e-04,X2.0,12347
2015-01-08,14:00,14:05,14:10,1.0e-05,B1.0,12348
"""

MOCK_CME_CSV = """date,lasco,speed,width,location,mass
2015-01-01,LASCO-C2,450,120,W90,1.2e12
2015-01-02,LASCO-C2,800,180,E30,2.5e12
2015-01-05,LASCO-C2,1200,240,W180,3.8e12
"""

MOCK_DST_CSV = """date,dst,src
2015-01-01,-20,H
2015-01-02,-45,H
2015-01-05,-150,H
2015-01-06,-120,H
2015-01-08,-10,H
"""

MOCK_KP_CSV = """date,kp,src
2015-01-01,2.0,H
2015-01-02,4.0,H
2015-01-05,7.0,H
2015-01-06,6.0,H
2015-01-08,1.0,H
"""

class TestFullIngestAlignFlow(unittest.TestCase):
    """Integration test for the full download-and-align flow."""

    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        self.raw_dir = os.path.join(self.data_dir, "raw")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.contracts_dir = os.path.join(self.test_dir, "contracts")
        
        # Create directory structure
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.contracts_dir, exist_ok=True)

        # Create a minimal mock schema for validation
        self.schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "event_date": {"type": "string"},
                "flare_flux": {"type": "number"},
                "cme_speed": {"type": "number"},
                "dst_min": {"type": "number"},
                "is_recurrent": {"type": "boolean"}
            },
            "required": ["event_date"]
        }
        schema_path = os.path.join(self.contracts_dir, "aligned_event.schema.yaml")
        import yaml
        with open(schema_path, 'w') as f:
            yaml.dump(self.schema_content, f)

        # Patch the base directories in the modules
        self.original_data_dir = os.environ.get('DATA_DIR', None)
        os.environ['DATA_DIR'] = self.data_dir
        os.environ['CONTRACTS_DIR'] = self.contracts_dir

    def tearDown(self):
        """Clean up temporary directory."""
        if self.original_data_dir:
            os.environ['DATA_DIR'] = self.original_data_dir
        else:
            os.environ.pop('DATA_DIR', None)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('code.ingest.requests.get')
    @patch('code.ingest.ftplib.FTP')
    def test_full_ingest_align_flow(self, mock_ftp, mock_requests_get):
        """
        Test the full ingest and align flow.
        
        Assert:
        1. `data/processed/aligned_events.csv` exists.
        2. The file contains > 0 rows.
        3. The data is schema-valid.
        """
        # 1. Mock the network responses to return our representative data
        # Mock GOES Flare List (FTP simulation via requests or direct file content)
        # Since ingest.py uses FTP for GOES and HTTP for others, we mock both paths.
        
        # Mock FTP connection for GOES
        mock_ftp_instance = MagicMock()
        mock_ftp_instance.retrlines.side_effect = lambda cmd, callback: callback(MOCK_GOES_FLARE_CSV.strip())
        mock_ftp.return_value.__enter__ = lambda s: mock_ftp_instance
        mock_ftp.return_value.__exit__ = lambda s, *args: None

        # Mock HTTP requests for CME, Dst, Kp
        mock_resp_cme = MagicMock()
        mock_resp_cme.text = MOCK_CME_CSV.strip()
        mock_resp_cme.status_code = 200
        
        mock_resp_dst = MagicMock()
        mock_resp_dst.text = MOCK_DST_CSV.strip()
        mock_resp_dst.status_code = 200

        mock_resp_kp = MagicMock()
        mock_resp_kp.text = MOCK_KP_CSV.strip()
        mock_resp_kp.status_code = 200

        # Patch requests.get to return appropriate mocks based on URL
        def mock_get_side_effect(url, *args, **kwargs):
            if 'cme' in url.lower() or 'lasco' in url.lower():
                return mock_resp_cme
            elif 'dst' in url.lower():
                return mock_resp_dst
            elif 'kp' in url.lower():
                return mock_resp_kp
            return MagicMock(status_code=404)

        mock_requests_get.side_effect = mock_get_side_effect

        # 2. Execute Ingestion (Simulated)
        # We call the specific fetch functions directly to ensure they write to our temp dir
        # Note: In a real run, these are called by main() in ingest.py
        # For this integration test, we invoke the logic that would be triggered.
        
        # Ensure directories exist
        ensure_directories()

        # Fetch and write raw data (mocked)
        # We assume the ingest.py functions write to the paths defined in the environment
        # or hardcoded relative paths. We patch the paths to point to our temp dir.
        
        with patch('code.ingest.DATA_DIR', self.data_dir):
            with patch('code.ingest.RAW_DIR', self.raw_dir):
                with patch('code.ingest.PROCESSED_DIR', self.processed_dir):
                    # Call the fetch functions
                    # These functions are expected to write to data/raw/
                    fetch_goess_flare_list()
                    fetch_cme_catalog()
                    fetch_dst_indices_http()
                    fetch_kp_indices_http()

        # 3. Execute Alignment
        # Load the raw data (now written to disk) and align
        # We call align_events directly
        with patch('code.align.DATA_DIR', self.data_dir):
            with patch('code.align.RAW_DIR', self.raw_dir):
                with patch('code.align.PROCESSED_DIR', self.processed_dir):
                    # Run alignment
                    aligned_df = align_events()
                    
                    # Flag recurrent activity
                    aligned_df = flag_recurrent_activity(aligned_df)
                    
                    # Write output
                    output_path = os.path.join(self.processed_dir, "aligned_events.csv")
                    write_aligned_events(aligned_df, output_path)

        # 4. Assertions
        aligned_csv = os.path.join(self.processed_dir, "aligned_events.csv")
        
        # Assert file exists
        self.assertTrue(os.path.exists(aligned_csv), 
                        f"aligned_events.csv was not created at {aligned_csv}")
        
        # Assert file has content
        df = pd.read_csv(aligned_csv)
        self.assertGreater(len(df), 0, "aligned_events.csv is empty")
        
        # Assert schema validity (basic check)
        # Load schema and validate records
        schema = load_schema(os.path.join(self.contracts_dir, "aligned_event.schema.yaml"))
        # Note: validate_aligned_events expects a file path or records
        is_valid, errors = validate_aligned_events(aligned_csv, schema)
        self.assertTrue(is_valid, f"Schema validation failed: {errors}")

        # 5. Filter Analysis Subset (Optional but good for flow)
        # This ensures the downstream task (T016b) can run
        subset_path = os.path.join(self.processed_dir, "analysis_subset.csv")
        with patch('code.filter_analysis_subset.PROCESSED_DIR', self.processed_dir):
            filter_non_recurrent_storms()
        
        self.assertTrue(os.path.exists(subset_path),
                        f"analysis_subset.csv was not created at {subset_path}")


if __name__ == '__main__':
    # Import pandas here to avoid circular imports if not needed at top level
    import pandas as pd
    unittest.main()
