"""
Unit tests for T017: NaN and State Explosion Validator.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, 'src')
from analysis.NaN_and_explosion_validator import (
    check_metrics_for_nan,
    detect_state_explosion_warnings,
    handle_state_explosion,
    validate_run_artifacts
)


class TestNaNCheck(unittest.TestCase):
    def test_clean_data(self):
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        is_clean, errors = check_metrics_for_nan(data)
        self.assertTrue(is_clean)
        self.assertEqual(len(errors), 0)

    def test_nan_data(self):
        data = pd.DataFrame({"a": [1, np.nan, 3], "b": [4.0, 5.0, 6.0]})
        is_clean, errors = check_metrics_for_nan(data)
        self.assertFalse(is_clean)
        self.assertTrue(any("Column 'a'" in e for e in errors))

    def test_inf_data(self):
        data = pd.DataFrame({"a": [1, np.inf, 3], "b": [4.0, 5.0, 6.0]})
        is_clean, errors = check_metrics_for_nan(data)
        self.assertFalse(is_clean)
        self.assertTrue(any("Column 'a'" in e for e in errors))

    def test_empty_list(self):
        is_clean, errors = check_metrics_for_nan([])
        self.assertTrue(is_clean)
        self.assertEqual(len(errors), 0)


class TestStateExplosionDetection(unittest.TestCase):
    def test_no_warnings(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("INFO: Run started\n")
            f.write("INFO: Step 1 complete\n")
            f.name
            path = f.name
        
        try:
            warnings = detect_state_explosion_warnings(path)
            self.assertEqual(len(warnings), 0)
        finally:
            os.unlink(path)

    def test_warning_detected(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("INFO: Run started\n")
            f.write("WARNING: State Explosion detected at step 100\n")
            f.name
            path = f.name
        
        try:
            warnings = detect_state_explosion_warnings(path)
            self.assertEqual(len(warnings), 1)
            self.assertIn("State Explosion", warnings[0]["content"])
        finally:
            os.unlink(path)

    def test_json_log_warning(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write('{"level": "INFO", "msg": "Started"}\n')
            f.write('{"level": "WARNING", "msg": "State Explosion", "step": 50}\n')
            f.name
            path = f.name
        
        try:
            warnings = detect_state_explosion_warnings(path)
            self.assertEqual(len(warnings), 1)
            self.assertEqual(warnings[0]["msg"], "State Explosion")
            self.assertEqual(warnings[0]["step"], 50)
        finally:
            os.unlink(path)


class TestStateExplosionHandling(unittest.TestCase):
    def test_handle_flag_updates_metrics(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("step,coherence\n1,0.9\n2,0.8\n")
            metrics_path = f.name

        warnings = [{"content": "Test explosion"}]
        
        result = handle_state_explosion(warnings, metrics_path, action="flag")
        
        self.assertTrue(result)
        
        # Verify file was updated
        df = pd.read_csv(metrics_path)
        self.assertIn("is_unstable", df.columns)
        self.assertTrue(df["is_unstable"].all())
        
        os.unlink(metrics_path)

    def test_handle_terminate_returns_false(self):
        warnings = [{"content": "Test explosion"}]
        result = handle_state_explosion(warnings, action="terminate")
        self.assertFalse(result)

    def test_handle_ignore_returns_true(self):
        warnings = [{"content": "Test explosion"}]
        result = handle_state_explosion(warnings, action="ignore")
        self.assertTrue(result)


class TestValidateRunArtifacts(unittest.TestCase):
    def test_full_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run_001"
            run_dir.mkdir()
            
            # Create clean metrics
            metrics = run_dir / "metrics.csv"
            pd.DataFrame({"step": [1], "coherence": [0.9]}).to_csv(metrics, index=False)
            
            # Create clean log
            log = run_dir / "run.log"
            with open(log, 'w') as f:
                f.write("INFO: Run completed successfully\n")
            
            result = validate_run_artifacts("run_001", base_dir=tmpdir)
            
            self.assertEqual(result["overall_status"], "PASS")
            self.assertTrue(result["nan_check_passed"])
            self.assertEqual(result["run_status"], "stable")

    def test_nan_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run_002"
            run_dir.mkdir()
            
            # Create metrics with NaN
            metrics = run_dir / "metrics.csv"
            pd.DataFrame({"step": [1], "coherence": [np.nan]}).to_csv(metrics, index=False)
            
            # Create clean log
            log = run_dir / "run.log"
            with open(log, 'w') as f:
                f.write("INFO: Run completed\n")
            
            result = validate_run_artifacts("run_002", base_dir=tmpdir)
            
            self.assertEqual(result["overall_status"], "FAIL")
            self.assertFalse(result["nan_check_passed"])

    def test_explosion_terminate_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run_003"
            run_dir.mkdir()
            
            # Create clean metrics
            metrics = run_dir / "metrics.csv"
            pd.DataFrame({"step": [1], "coherence": [0.9]}).to_csv(metrics, index=False)
            
            # Create log with explosion warning
            log = run_dir / "run.log"
            with open(log, 'w') as f:
                f.write("WARNING: State Explosion detected\n")
            
            result = validate_run_artifacts("run_003", base_dir=tmpdir, action="terminate")
            
            self.assertEqual(result["overall_status"], "FAIL")
            self.assertEqual(result["run_status"], "terminated")


if __name__ == "__main__":
    unittest.main()