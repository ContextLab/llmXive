"""
Integration tests for model training pipeline, specifically Leave-One-Cycle-Out (LOCO) CV logic.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Import the functions we are testing
from models.train import run_loco_cv, load_preprocessed_data, prepare_features


def create_mock_preprocessed_data(tmp_path: Path) -> Path:
    """
    Creates a mock preprocessed parquet file with known cycle IDs
    to test the LOCO logic deterministically.
    """
    # Create a synthetic dataset with distinct, known cycles
    # We need enough data per cycle to train and test
    cycles = [1, 2, 3, 4]
    data = []
    for c_id in cycles:
        # Generate 100 rows per cycle
        n_rows = 100
        years = np.linspace(1900 + (c_id * 11), 1900 + (c_id * 11) + 10, n_rows)
        gsn = np.random.uniform(10, 100, n_rows)
        # TSI is loosely correlated with GSN for this mock
        tsi = 1361.0 + (gsn * 0.005) + np.random.normal(0, 0.1, n_rows)
        
        df_cycle = pd.DataFrame({
            'date': pd.to_datetime(years, format='%Y'),
            'gsn': gsn,
            'tsi': tsi,
            'cycle_id': c_id
        })
        data.append(df_cycle)
    
    full_df = pd.concat(data, ignore_index=True)
    
    output_path = tmp_path / "preprocessed_data.parquet"
    full_df.to_parquet(output_path)
    return output_path


class TestLOCO_CV_Logic:
    """
    Integration tests for the Leave-One-Cycle-Out cross-validation logic.
    Verifies that the correct cycle is held out and the model trains on the rest.
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup temporary directory for test artifacts."""
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)
        yield
        shutil.rmtree(self.tmp_dir)

    def test_loco_cv_logic(self, setup_and_teardown):
        """
        Verify cycle holdout logic:
        1. Ensure that for each iteration, exactly one cycle is excluded from training.
        2. Ensure the held-out cycle is used for validation.
        3. Ensure the report contains metrics for every cycle.
        """
        # 1. Setup: Create mock data with 4 distinct cycles
        data_path = create_mock_preprocessed_data(self.tmp_path)
        
        # Ensure the data file exists
        assert data_path.exists(), "Mock preprocessed data file was not created."

        # 2. Execute: Run LOCO CV
        # We pass the path to our mock data
        report = run_loco_cv(
            data_path=str(data_path),
            output_dir=str(self.tmp_path),
            report_filename="cv_test_report.json"
        )

        # 3. Assertions
        
        # A. Verify report structure
        assert report is not None, "LOCO CV should return a report dictionary."
        assert "results" in report, "Report must contain 'results' key."
        assert "methodology" in report, "Report must contain 'methodology' key."
        
        results = report["results"]
        assert isinstance(results, list), "Results must be a list of per-cycle metrics."
        
        # B. Verify all cycles were processed
        # We created cycles 1, 2, 3, 4
        processed_cycles = {r["cycle_id"] for r in results}
        expected_cycles = {1, 2, 3, 4}
        assert processed_cycles == expected_cycles, (
            f"LOCO CV must process all cycles. Expected {expected_cycles}, got {processed_cycles}"
        )

        # C. Verify metrics exist for each cycle
        for r in results:
            assert "cycle_id" in r, "Each result must have cycle_id"
            assert "rmse" in r, "Each result must have RMSE"
            assert "r_squared" in r, "Each result must have R²"
            assert "train_size" in r, "Each result must have train_size"
            assert "val_size" in r, "Each result must have val_size"
            
            # Sanity check: Train size should be larger than val size
            # (3 cycles vs 1 cycle)
            assert r["train_size"] > r["val_size"], (
                f"Train size ({r['train_size']}) must be greater than val size ({r['val_size']})"
            )
            
            # Sanity check: RMSE should be a positive number
            assert r["rmse"] > 0, "RMSE must be positive"
            # Sanity check: R² should be <= 1 (though can be negative for bad models)
            assert r["r_squared"] <= 1.0, "R² cannot be greater than 1"

        # D. Verify the holdout logic specifically
        # We can inspect the 'train_size' to ensure it matches 3 cycles worth of data
        # In our mock, each cycle has 100 rows. Total = 400.
        # Train set should be 300 rows (3 cycles), Val set 100 rows (1 cycle).
        for r in results:
            assert r["train_size"] == 300, (
                f"Train size should be 300 (3 cycles * 100 rows), got {r['train_size']}"
            )
            assert r["val_size"] == 100, (
                f"Val size should be 100 (1 cycle * 100 rows), got {r['val_size']}"
            )

        # E. Verify the report was saved to disk
        expected_report_path = self.tmp_path / "cv_test_report.json"
        assert expected_report_path.exists(), "Report file must be saved to disk."
        
        # F. Verify the saved JSON content matches the returned object
        with open(expected_report_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["results"] == results, "Saved report must match returned report."

    def test_loco_cv_handles_single_cycle(self, setup_and_teardown):
        """
        Edge case: If data only has one cycle, LOCO CV cannot function normally
        (training set would be empty). The function should handle this gracefully
        or raise a specific error.
        """
        # Create data with only 1 cycle
        cycles = [1]
        data = []
        for c_id in cycles:
            n_rows = 100
            years = np.linspace(1900, 1910, n_rows)
            gsn = np.random.uniform(10, 100, n_rows)
            tsi = 1361.0 + (gsn * 0.005)
            
            df_cycle = pd.DataFrame({
                'date': pd.to_datetime(years, format='%Y'),
                'gsn': gsn,
                'tsi': tsi,
                'cycle_id': c_id
            })
            data.append(df_cycle)
        
        full_df = pd.concat(data, ignore_index=True)
        data_path = self.tmp_path / "single_cycle.parquet"
        full_df.to_parquet(data_path)

        # Expect an error or empty result because we can't train on 0 samples
        # The implementation should detect this.
        # Based on standard LOCO logic, if N=1, train_size=0 -> Error.
        with pytest.raises(ValueError) as exc_info:
            run_loco_cv(
                data_path=str(data_path),
                output_dir=str(self.tmp_path),
                report_filename="cv_single_cycle.json"
            )
        
        # Verify the error message is informative
        assert "insufficient" in str(exc_info.value).lower() or "at least two" in str(exc_info.value).lower(), (
            "LOCO CV should raise a clear error when only one cycle is present."
        )

    def test_loco_cv_report_structure(self, setup_and_teardown):
        """
        Verify the report contains the required methodology description and
        associational framing as per project constraints.
        """
        data_path = create_mock_preprocessed_data(self.tmp_path)
        report = run_loco_cv(
            data_path=str(data_path),
            output_dir=str(self.tmp_path),
            report_filename="cv_structure_report.json"
        )

        assert "methodology" in report
        methodology = report["methodology"]
        
        # Check for required fields in methodology
        assert "validation_scheme" in methodology
        assert methodology["validation_scheme"] == "Leave-One-Cycle-Out (LOCO)"
        
        # Check for associational framing note
        assert "framing" in methodology
        assert "associational" in methodology["framing"].lower(), (
            "Methodology must explicitly state findings are associational."
        )