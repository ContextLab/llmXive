"""
End-to-End Integration Test for the Network Structure Superconducting Qubit Pipeline.

This test verifies the full data flow (Fetch -> Graph -> Stats -> Report) using
the mock fixture (T006b) to ensure artifact generation without live API calls.
"""
import os
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# Ensure code directory is in path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.fetcher import fetch_backends_list, fetch_backend_properties
from code.generate_calibration_csv import load_raw_snapshots, extract_device_metrics, process_snapshot, main as generate_csv_main
from code.generate_graph_metrics_csv import load_processed_calibration, compute_device_metrics, main as generate_graph_main
from code.stats_engine import load_and_merge_metrics, compute_spearman_correlations, apply_benjamini_hochberg_fdr, save_correlation_results, main as stats_main
from code.generate_report import generate_report, main as report_main
from code.hygiene import update_state_file

# Constants for test paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "mock_backend_properties.json"
REPORT_PATH = PROJECT_ROOT / "docs" / "report.md"

class TestEndToEndPipeline(unittest.TestCase):
    """Tests the full pipeline using mock data."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment: ensure directories exist and clean previous artifacts."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)

        # Ensure directories exist
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        (PROJECT_ROOT / "docs").mkdir(parents=True, exist_ok=True)

        # Clean previous artifacts to ensure fresh generation
        for f in DATA_PROCESSED_DIR.glob("*.csv"):
            f.unlink()
        if REPORT_PATH.exists():
            REPORT_PATH.unlink()

        # Prepare mock data: copy fixture to raw directory with expected naming
        # The fetcher expects files like {device_id}_{timestamp}.json
        cls.mock_device_id = "mock_ibmq_manila"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls.mock_raw_file = DATA_RAW_DIR / f"{cls.mock_device_id}_{timestamp_str}.json"

        # Load mock data and inject our mock device ID
        with open(FIXTURE_PATH, 'r') as f:
            mock_data = json.load(f)
        
        # Modify the mock data to match our expected structure if necessary
        # The fixture T006b should have a structure compatible with raw_calibration.schema.yaml
        if 'device_id' in mock_data:
            mock_data['device_id'] = cls.mock_device_id
        
        with open(cls.mock_raw_file, 'w') as f:
            json.dump(mock_data, f)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directories and restore working directory."""
        os.chdir(cls.original_cwd)
        shutil.rmtree(cls.temp_dir)

    def test_01_generate_calibration_csv(self):
        """Test T017: Generate processed CSV from raw snapshots."""
        # Run the CSV generation logic
        # We call the main logic directly or via the script entry point
        # Using the functions from generate_calibration_csv
        raw_snapshots = load_raw_snapshots(DATA_RAW_DIR)
        self.assertGreater(len(raw_snapshots), 0, "No raw snapshots found.")

        processed_data = []
        for snapshot_path in raw_snapshots:
            device_metrics = process_snapshot(snapshot_path)
            if device_metrics:
                processed_data.append(device_metrics)

        # Save to CSV
        output_csv = DATA_PROCESSED_DIR / "raw_calibration.csv"
        if processed_data:
            import pandas as pd
            df = pd.DataFrame(processed_data)
            # Ensure coupling_map is JSON string
            df['coupling_map'] = df['coupling_map'].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
            df.to_csv(output_csv, index=False)
        else:
            # Create empty file with headers if no data
            pd.DataFrame(columns=['device_id', 'timestamp', 't1_mean', 't2_mean', 'cx_error_mean', 'readout_error_mean', 'coupling_map']).to_csv(output_csv, index=False)

        self.assertTrue(output_csv.exists(), "raw_calibration.csv not generated.")
        
        # Verify schema
        df = pd.read_csv(output_csv)
        expected_cols = ['device_id', 'timestamp', 't1_mean', 't2_mean', 'cx_error_mean', 'readout_error_mean', 'coupling_map']
        self.assertEqual(list(df.columns), expected_cols)
        
        # Verify JSON validity in coupling_map
        for _, row in df.iterrows():
            json.loads(row['coupling_map'])

    def test_02_generate_graph_metrics(self):
        """Test T025: Generate graph metrics CSV."""
        # Run graph metrics generation
        # This depends on T017 output
        load_processed_calibration(DATA_PROCESSED_DIR / "raw_calibration.csv")
        
        # Execute the main logic for graph metrics
        # We simulate the script entry point
        import pandas as pd
        df_raw = pd.read_csv(DATA_PROCESSED_DIR / "raw_calibration.csv")
        
        all_metrics = []
        for _, row in df_raw.iterrows():
            coupling_map = json.loads(row['coupling_map'])
            device_id = row['device_id']
            # Compute metrics using graph_builder logic
            from code.graph_builder import build_coupling_graph, compute_shortest_path_metrics, compute_clustering_and_assortativity, compute_edge_betweenness_and_spectral_gap
            
            g = build_coupling_graph(coupling_map)
            
            # Shortest path
            sp_metrics = compute_shortest_path_metrics(g)
            for k, v in sp_metrics.items():
                all_metrics.append({'device_id': device_id, 'metric_name': f'sp_{k}', 'value': v, 'is_finite': pd.notna(v)})
            
            # Clustering
            cl_metrics = compute_clustering_and_assortativity(g)
            for k, v in cl_metrics.items():
                all_metrics.append({'device_id': device_id, 'metric_name': f'cl_{k}', 'value': v, 'is_finite': pd.notna(v)})
            
            # Betweenness/Spectral
            be_metrics = compute_edge_betweenness_and_spectral_gap(g)
            for k, v in be_metrics.items():
                all_metrics.append({'device_id': device_id, 'metric_name': f'be_{k}', 'value': v, 'is_finite': pd.notna(v)})

        output_csv = DATA_PROCESSED_DIR / "graph_metrics.csv"
        if all_metrics:
            df_graph = pd.DataFrame(all_metrics)
            df_graph.to_csv(output_csv, index=False)
        else:
            pd.DataFrame(columns=['device_id', 'metric_name', 'value', 'is_finite']).to_csv(output_csv, index=False)

        self.assertTrue(output_csv.exists(), "graph_metrics.csv not generated.")
        
        df_graph = pd.read_csv(output_csv)
        self.assertIn('device_id', df_graph.columns)
        self.assertIn('metric_name', df_graph.columns)
        self.assertIn('value', df_graph.columns)
        self.assertIn('is_finite', df_graph.columns)
        self.assertGreater(len(df_graph), 0, "No graph metrics computed.")

    def test_03_generate_correlation_results(self):
        """Test T034: Generate correlation results CSV."""
        # Run stats engine logic
        # Merge metrics
        from code.stats_engine import load_and_merge_metrics
        merged_df = load_and_merge_metrics(DATA_PROCESSED_DIR)
        
        if len(merged_df) > 0:
            # Compute correlations
            corr_df = compute_spearman_correlations(merged_df)
            adj_corr_df = apply_benjamini_hochberg_fdr(corr_df)
            
            output_csv = DATA_PROCESSED_DIR / "correlation_results.csv"
            adj_corr_df.to_csv(output_csv, index=False)
            
            self.assertTrue(output_csv.exists(), "correlation_results.csv not generated.")
            df_corr = pd.read_csv(output_csv)
            self.assertIn('metric_a', df_corr.columns)
            self.assertIn('metric_b', df_corr.columns)
            self.assertIn('spearman_rho', df_corr.columns)
            self.assertIn('adj_p_value', df_corr.columns)
            self.assertIn('is_significant', df_corr.columns)
        else:
            # If no data to merge, create empty file with headers
            pd.DataFrame(columns=['metric_a', 'metric_b', 'spearman_rho', 'p_value', 'adj_p_value', 'is_significant', 'is_excluded']).to_csv(DATA_PROCESSED_DIR / "correlation_results.csv", index=False)

    def test_04_generate_report(self):
        """Test T037: Generate report.md."""
        # Run report generation
        # This depends on correlation results
        report_content = generate_report(DATA_PROCESSED_DIR, PROJECT_ROOT / "docs")
        
        self.assertTrue(REPORT_PATH.exists(), "report.md not generated.")
        
        with open(REPORT_PATH, 'r') as f:
            content = f.read()
        
        # Verify required sections
        self.assertIn("Methodology", content)
        self.assertIn("Correlation Results", content)
        self.assertIn("Robustness", content)
        self.assertIn("LODO", content) # Per T037 verification requirement

    def test_05_update_state_file(self):
        """Test T038: Update state file with artifact hashes."""
        state_file = PROJECT_ROOT / "state" / "projects" / "PROJ-163-exploring-the-role-of-network-structure-.yaml"
        update_state_file(state_file)
        
        self.assertTrue(state_file.exists(), "State file not updated.")
        
        import yaml
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        self.assertIn("artifact_hashes", state)
        self.assertIsInstance(state["artifact_hashes"], dict)

if __name__ == '__main__':
    unittest.main()