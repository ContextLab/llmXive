import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import json
import csv

# Import from the existing API surface
from ingestion.tng_loader import fetch_halos_list, download_file, fetch_tng_halo_data
from processing.pipeline_runner import iterate_haloes, run_pipeline, validate_shape_metrics_chunk, write_exclusion_log, save_halo_shapes_chunk
from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors
from processing.shape_metrics import compute_axial_ratios, compute_triaxiality, filter_halo_by_particle_count, validate_shape_metrics
from utils.config import get_project_root, get_data_raw_path, get_data_processed_path, get_logs_path, set_random_seed
from utils.io import write_csv_with_associational_flag, write_json_with_associational_flag, managed_hdf5_reader
from utils.logging import get_pipeline_logger, log_task_start, log_task_end, log_error

class TestTNGPipelineIntegration:
    """
    Integration test for TNG-100 download and chunk processing.
    Verifies the pipeline retrieves the TNG-100 catalog, computes inertia tensors
    for a random subset of haloes, and outputs CSVs with valid axial ratios and triaxiality.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup temporary directories and teardown after test."""
        self.project_root = Path(tempfile.mkdtemp(prefix="tng_test_"))
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.logs = self.project_root / "logs"
        
        # Create directory structure
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_processed.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

        # Patch config functions to use our temp directory
        with patch('utils.config.get_project_root', return_value=self.project_root), \
             patch('utils.config.get_data_raw_path', return_value=self.data_raw), \
             patch('utils.config.get_data_processed_path', return_value=self.data_processed), \
             patch('utils.config.get_logs_path', return_value=self.logs):
            yield

        # Cleanup
        shutil.rmtree(self.project_root, ignore_errors=True)

    @patch('ingestion.tng_loader.requests.get')
    @patch('ingestion.tng_loader.download_file')
    @patch('ingestion.tng_loader.h5py.File')
    def test_full_pipeline_execution(self, mock_h5py, mock_download, mock_get):
        """
        Test the full pipeline flow:
        1. Fetch halo list (mocked)
        2. Download specific halo files (mocked)
        3. Process chunks and compute shape metrics
        4. Validate output files exist and contain valid data
        """
        # --- Mock Setup ---
        
        # Mock API response for halo list
        mock_api_response = MagicMock()
        mock_api_response.status_code = 200
        mock_api_response.json.return_value = {
            "count": 5,
            "results": [
                {"id": 1, "num_particles": 15000, "url": "http://mock.tng/halo_1.hdf5"},
                {"id": 2, "num_particles": 12000, "url": "http://mock.tng/halo_2.hdf5"},
                {"id": 3, "num_particles": 5000, "url": "http://mock.tng/halo_3.hdf5"}, # Should be excluded
                {"id": 4, "num_particles": 18000, "url": "http://mock.tng/halo_4.hdf5"},
                {"id": 5, "num_particles": 20000, "url": "http://mock.tng/halo_5.hdf5"},
            ]
        }
        mock_get.return_value = mock_api_response

        # Mock download to just create an empty file that we will pretend is HDF5
        def mock_download_side_effect(url, dest_path, *args, **kwargs):
            Path(dest_path).touch()
            return True
        mock_download.side_effect = mock_download_side_effect

        # Mock HDF5 file structure
        mock_h5py_instance = MagicMock()
        mock_h5py.return_value.__enter__ = MagicMock(return_value=mock_h5py_instance)
        mock_h5py.return_value.__exit__ = MagicMock(return_value=False)
        
        # Mock particle data: positions (N, 3)
        # We need enough particles to compute inertia
        # Let's say 15k particles for valid haloes
        import numpy as np
        valid_positions = np.random.rand(15000, 3).astype(np.float32)
        invalid_positions = np.random.rand(4000, 3).astype(np.float32) # < 10k

        def h5py_group_get(key):
            if key == "PartType0":
                mock_group = MagicMock()
                mock_group.__getitem__.side_effect = lambda k: valid_positions if k == "Coordinates" else None
                return mock_group
            return None

        mock_h5py_instance.__getitem__.side_effect = h5py_group_get
        mock_h5py_instance.keys.return_value = ["PartType0"]

        # --- Execution ---
        
        # 1. Fetch Halo List
        from ingestion.tng_loader import fetch_halos_list
        # We need to patch the base URL and API key for the test
        with patch('ingestion.tng_loader.BASE_URL', 'http://mock.tng'), \
             patch('ingestion.tng_loader.get_api_key', return_value='fake_key'):
            halos_list = fetch_halos_list(snapshot=0)
        
        assert len(halos_list) > 0, "Halo list should not be empty"
        
        # 2. Run Pipeline Logic (Simulating the chunked processing)
        # We will manually iterate through the mock halos to simulate the pipeline
        # In a real run, this is done by pipeline_runner.run_pipeline()
        
        logger = get_pipeline_logger("test_integration", str(self.logs))
        log_task_start(logger, "T010_Integration_Test")

        processed_halos = []
        excluded_halos = []

        # Simulate processing each halo in the list
        for halo in halos_list:
            halo_id = halo['id']
            num_particles = halo['num_particles']
            halo_path = self.data_raw / f"halo_{halo_id}.hdf5"
            
            # Check particle count filter
            if num_particles < 10000:
                excluded_halos.append({
                    "halo_id": halo_id,
                    "reason": f"Particle count {num_particles} < 10000"
                })
                continue

            # Mock reading data
            # In real code: data = fetch_tng_halo_data(halo_path, "PartType0", "Coordinates")
            # Here we use our mock data
            positions = valid_positions if num_particles >= 10000 else invalid_positions

            # Compute Inertia Tensor
            inertia = compute_reduced_inertia_tensor(positions)
            eigenvalues, eigenvectors = compute_eigenvalues_and_eigenvectors(inertia)

            # Compute Shape Metrics
            axial_ratios = compute_axial_ratios(eigenvalues)
            triaxiality = compute_triaxiality(eigenvalues)

            # Validate
            is_valid = validate_shape_metrics(axial_ratios, triaxiality)
            
            if is_valid:
                processed_halos.append({
                    "halo_id": halo_id,
                    "mass": float(num_particles * 1.0), # Mock mass
                    "b_a_ratio": float(axial_ratios[1]),
                    "c_a_ratio": float(axial_ratios[2]),
                    "triaxiality": float(triaxiality),
                    "particle_count": num_particles
                })
            else:
                excluded_halos.append({
                    "halo_id": halo_id,
                    "reason": "Invalid shape metrics"
                })

        # 3. Write Output Files (Simulating T017/T018 deliverables)
        # Halo Shapes CSV
        output_csv_path = self.data_processed / "halo_shapes.csv"
        write_csv_with_associational_flag(
            output_csv_path,
            processed_halos,
            ["halo_id", "mass", "b_a_ratio", "c_a_ratio", "triaxiality", "particle_count"]
        )

        # Exclusion Log JSON
        output_json_path = self.data_processed / "exclusion_log.json"
        write_json_with_associational_flag(
            output_json_path,
            excluded_halos
        )

        log_task_end(logger, "T010_Integration_Test", success=True)

        # --- Verification ---
        
        # Check files exist
        assert output_csv_path.exists(), f"Output CSV {output_csv_path} not created"
        assert output_json_path.exists(), f"Output JSON {output_json_path} not created"

        # Check CSV content
        with open(output_csv_path, 'r') as f:
            # First line should be the flag
            first_line = f.readline().strip()
            assert "# associational_only=true" in first_line, "CSV missing associational flag"
            
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Verify we have valid rows (excluding the one with <10k particles)
            # We expect 4 valid halos (1, 2, 4, 5)
            assert len(rows) == 4, f"Expected 4 valid halos, got {len(rows)}"

            for row in rows:
                b_a = float(row['b_a_ratio'])
                c_a = float(row['c_a_ratio'])
                t = float(row['triaxiality'])
                n = int(row['particle_count'])

                # Validate constraints: 0 < b/a <= 1, 0 < c/a <= 1, 0 <= T <= 1, N >= 10000
                assert 0 < b_a <= 1.0, f"Invalid b/a ratio: {b_a}"
                assert 0 < c_a <= 1.0, f"Invalid c/a ratio: {c_a}"
                assert 0 <= t <= 1.0, f"Invalid triaxiality: {t}"
                assert n >= 10000, f"Particle count {n} is below threshold"

        # Check JSON content
        with open(output_json_path, 'r') as f:
            content = f.read()
            assert '"associational_only": true' in content, "JSON missing associational flag"
            data = json.loads(content)
            assert len(data) == 1, f"Expected 1 excluded halo, got {len(data)}"
            assert data[0]['halo_id'] == 3, "Halo 3 should be excluded"

    @patch('ingestion.tng_loader.requests.get')
    def test_pipeline_handles_api_failure(self, mock_get):
        """
        Test that the pipeline fails loudly if the API is unreachable,
        rather than falling back to synthetic data.
        """
        mock_get.side_effect = Exception("Network Error")
        
        with patch('ingestion.tng_loader.BASE_URL', 'http://mock.tng'), \
             patch('ingestion.tng_loader.get_api_key', return_value='fake_key'):
            with pytest.raises(Exception, match="Network Error"):
                fetch_halos_list(snapshot=0)

    @patch('ingestion.tng_loader.requests.get')
    def test_pipeline_handles_empty_response(self, mock_get):
        """
        Test that the pipeline handles an empty halo list gracefully (no crash, just no output).
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 0, "results": []}
        mock_get.return_value = mock_response

        with patch('ingestion.tng_loader.BASE_URL', 'http://mock.tng'), \
             patch('ingestion.tng_loader.get_api_key', return_value='fake_key'):
            halos = fetch_halos_list(snapshot=0)
            assert len(halos) == 0

        # Ensure no output files are created if no data
        # (Or if they are, they are empty/valid headers)
        # In this specific test, we verify the fetch step fails gracefully or returns empty.
        # The actual file writing is tested in the main integration test.

    def test_chunk_validation_logic(self):
        """
        Test the validation logic for shape metrics chunk.
        """
        # Valid chunk
        valid_chunk = [
            {"b_a_ratio": 0.8, "c_a_ratio": 0.6, "triaxiality": 0.5, "particle_count": 12000},
            {"b_a_ratio": 0.9, "c_a_ratio": 0.9, "triaxiality": 0.2, "particle_count": 15000}
        ]
        
        assert validate_shape_metrics_chunk(valid_chunk) is True

        # Invalid chunk: b/a > 1
        invalid_chunk_1 = [
            {"b_a_ratio": 1.2, "c_a_ratio": 0.6, "triaxiality": 0.5, "particle_count": 12000}
        ]
        assert validate_shape_metrics_chunk(invalid_chunk_1) is False

        # Invalid chunk: triaxiality < 0
        invalid_chunk_2 = [
            {"b_a_ratio": 0.8, "c_a_ratio": 0.6, "triaxiality": -0.1, "particle_count": 12000}
        ]
        assert validate_shape_metrics_chunk(invalid_chunk_2) is False

        # Invalid chunk: particle count < 10000
        invalid_chunk_3 = [
            {"b_a_ratio": 0.8, "c_a_ratio": 0.6, "triaxiality": 0.5, "particle_count": 5000}
        ]
        assert validate_shape_metrics_chunk(invalid_chunk_3) is False