import os
import tempfile
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from data.extract_ground_truth import RTPurboResult, save_to_hdf5, main

class TestAnomalyDetection:
    """
    Integration test for anomaly detection in RTPurbo extraction.
    Verifies that documents with zero RTPurbo tokens are flagged and excluded.
    """

    def test_anomaly_flagging_and_exclusion(self):
        """
        Test that documents with zero selected indices are flagged as anomalies,
        logged to CSV, and excluded from the HDF5 output.
        """
        # Create mock results
        results = [
            RTPurboResult(
                doc_id="doc_valid_1",
                total_tokens=100,
                selected_indices=[1, 5, 10],
                is_anomaly=False
            ),
            RTPurboResult(
                doc_id="doc_anomaly_1",
                total_tokens=0,
                selected_indices=[],
                is_anomaly=True,
                anomaly_reason="Empty token sequence"
            ),
            RTPurboResult(
                doc_id="doc_anomaly_2",
                total_tokens=50,
                selected_indices=[],
                is_anomaly=True,
                anomaly_reason="Zero RTPurbo tokens selected"
            ),
            RTPurboResult(
                doc_id="doc_valid_2",
                total_tokens=200,
                selected_indices=[2, 4, 6],
                is_anomaly=False
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            h5_path = os.path.join(tmpdir, "attention_maps.h5")
            csv_path = os.path.join(tmpdir, "anomalies.csv")

            # Run the save function
            save_to_hdf5(results, h5_path, csv_path)

            # Verify anomaly CSV
            assert os.path.exists(csv_path), "Anomalies CSV not created"
            df_anomalies = pd.read_csv(csv_path)
            
            assert len(df_anomalies) == 2, f"Expected 2 anomalies, got {len(df_anomalies)}"
            assert set(df_anomalies['doc_id']) == {"doc_anomaly_1", "doc_anomaly_2"}
            assert "Empty token sequence" in df_anomalies['reason'].values
            assert "Zero RTPurbo tokens selected" in df_anomalies['reason'].values

            # Verify HDF5 contains only valid results
            import h5py
            assert os.path.exists(h5_path), "HDF5 file not created"
            
            with h5py.File(h5_path, 'r') as f:
                # Check number of groups (should be 2 valid results)
                assert len(f.keys()) == 2, f"Expected 2 valid groups in HDF5, got {len(f.keys())}"
                
                # Verify doc_ids
                doc_ids = [f[key].attrs['doc_id'] for key in f.keys()]
                assert "doc_valid_1" in doc_ids
                assert "doc_valid_2" in doc_ids
                assert "doc_anomaly_1" not in doc_ids
                assert "doc_anomaly_2" not in doc_ids

    def test_empty_results_list(self):
        """
        Test handling of an empty results list.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            h5_path = os.path.join(tmpdir, "attention_maps.h5")
            csv_path = os.path.join(tmpdir, "anomalies.csv")

            save_to_hdf5([], h5_path, csv_path)

            assert os.path.exists(csv_path)
            df_anomalies = pd.read_csv(csv_path)
            assert len(df_anomalies) == 0

            import h5py
            with h5py.File(h5_path, 'r') as f:
                assert len(f.keys()) == 0
