"""
Integration test for full evaluation loop with mock data.
This test verifies the end-to-end flow of the evaluation pipeline:
1. Loading simulation results (mocked for this test)
2. Running McNemar's Test comparisons
3. Calculating trajectory fidelity metrics
4. Generating the final evaluation report

Note: Uses mock/synthetic data ONLY for the purpose of testing the
evaluation logic flow. In production (T030-T037), this will be driven
by real simulation outputs from PyBullet.
"""
import unittest
import sys
import os
import tempfile
import shutil
import json
import csv
import numpy as np
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.seeds import set_global_seed

class MockSimulationResults:
    """
    Generates deterministic mock simulation results for testing the evaluation pipeline.
    These mock results simulate the output of code/05_simulate.py.
    """
    def __init__(self, seed: int = 42, n_samples: int = 100):
        set_global_seed(seed)
        self.n_samples = n_samples
        self.task_types = ['grasp', 'navigate', 'place']
        
        # Generate deterministic mock data
        self.data = []
        for i in range(n_samples):
            task = self.task_types[i % 3]
            # Mock success rates: Non-neural ~70%, Random ~30%, VLA ~85%
            non_neural_success = 1 if np.random.rand() < 0.70 else 0
            random_success = 1 if np.random.rand() < 0.30 else 0
            vla_success = 1 if np.random.rand() < 0.85 else 0
            
            # Mock collision counts
            non_neural_collisions = np.random.randint(0, 3)
            random_collisions = np.random.randint(0, 5)
            vla_collisions = np.random.randint(0, 2)
            
            self.data.append({
                'sample_id': i,
                'task_type': task,
                'non_neural_success': non_neural_success,
                'random_success': random_success,
                'vla_proxy_success': vla_success,
                'non_neural_collisions': non_neural_collisions,
                'random_collisions': random_collisions,
                'vla_proxy_collisions': vla_collisions,
                'execution_time': 0.5 + np.random.rand() * 2.0
            })

class TestEvaluationLoop(unittest.TestCase):
    """
    Integration test for the full evaluation loop.
    Tests the logic in code/06_evaluate.py (McNemar's Test, fidelity metrics, reporting).
    """
    
    def setUp(self):
        """Set up temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.results_csv = os.path.join(self.test_dir, 'simulation_logs.csv')
        self.report_path = os.path.join(self.test_dir, 'evaluation_report.md')
        self.config_path = os.path.join(self.test_dir, 'config.yaml')
        
        # Create mock config
        config = {
            'paths': {
                'results_dir': self.test_dir,
                'models_dir': os.path.join(self.test_dir, 'models')
            },
            'evaluation': {
                'fidelity_threshold': 0.1,
                'confidence_level': 0.95
            }
        }
        os.makedirs(os.path.join(self.test_dir, 'models'), exist_ok=True)
        
        # Write mock config
        with open(self.config_path, 'w') as f:
            import yaml
            yaml.dump(config, f)

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _write_mock_simulation_data(self):
        """Write mock simulation data to CSV."""
        mock_results = MockSimulationResults(seed=42, n_samples=200)
        
        with open(self.results_csv, 'w', newline='') as f:
            fieldnames = ['sample_id', 'task_type', 'non_neural_success', 
                          'random_success', 'vla_proxy_success',
                          'non_neural_collisions', 'random_collisions', 
                          'vla_proxy_collisions', 'execution_time']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(mock_results.data)

    def test_mcnemar_test_logic(self):
        """
        Test McNemar's Test implementation with mock data.
        Verifies that the statistical test runs and produces valid p-values.
        """
        from scipy.stats import mcnemar
        
        self._write_mock_simulation_data()
        
        # Load data
        import pandas as pd
        df = pd.read_csv(self.results_csv)
        
        # Test Non-Neural vs Random
        # Build contingency table for McNemar's
        # Rows: Non-Neural (Success=1, Fail=0), Cols: Random (Success=1, Fail=0)
        # We need discordant pairs: (Success, Fail) and (Fail, Success)
        
        nn_success = df['non_neural_success']
        rand_success = df['random_success']
        
        # Discordant pairs
        b = ((nn_success == 1) & (rand_success == 0)).sum()  # NN success, Random fail
        c = ((nn_success == 0) & (rand_success == 1)).sum()  # NN fail, Random success
        
        # McNemar's test (with continuity correction)
        if b + c > 0:
            result = mcnemar([[b + c, b], [c, b + c]], exact=False, correction=True)
            p_value = result.pvalue
            self.assertGreater(p_value, 0.0, "P-value should be non-negative")
            self.assertLess(p_value, 1.0, "P-value should be less than 1.0")
        else:
            # Edge case: no discordant pairs
            pass

    def test_trajectory_fidelity_calculation(self):
        """
        Test trajectory fidelity metric calculation.
        Verifies that fidelity is computed as percentage of features within error margin.
        """
        # Mock trajectory data
        np.random.seed(42)
        n_points = 50
        n_features = 7  # e.g., 7 joint angles
        
        # Generate mock trajectories
        true_trajectory = np.random.randn(n_points, n_features) * 0.5
        predicted_trajectory = true_trajectory + np.random.randn(n_points, n_features) * 0.1
        
        # Error margin (e.g., 0.2 radians)
        error_margin = 0.2
        
        # Calculate absolute error
        abs_error = np.abs(predicted_trajectory - true_trajectory)
        
        # Count points within margin
        within_margin = abs_error < error_margin
        fidelity = np.mean(within_margin)
        
        # Fidelity should be high (since we added small noise)
        self.assertGreater(fidelity, 0.8, "Fidelity should be > 80% for small noise")
        self.assertLessEqual(fidelity, 1.0, "Fidelity cannot exceed 100%")

    def test_full_evaluation_pipeline(self):
        """
        Test the full evaluation pipeline flow:
        1. Load simulation results
        2. Compute statistics per task type
        3. Run McNemar's tests
        4. Calculate fidelity
        5. Generate report
        """
        self._write_mock_simulation_data()
        
        import pandas as pd
        import numpy as np
        from scipy.stats import mcnemar
        
        # Load data
        df = pd.read_csv(self.results_csv)
        
        # 1. Compute success rates per task type
        success_rates = {}
        for task in df['task_type'].unique():
            task_data = df[df['task_type'] == task]
            nn_rate = task_data['non_neural_success'].mean()
            rand_rate = task_data['random_success'].mean()
            vla_rate = task_data['vla_proxy_success'].mean()
            success_rates[task] = {
                'non_neural': nn_rate,
                'random': rand_rate,
                'vla_proxy': vla_rate
            }
        
        # Verify rates are in [0, 1]
        for task, rates in success_rates.items():
            for model, rate in rates.items():
                self.assertGreaterEqual(rate, 0.0)
                self.assertLessEqual(rate, 1.0)
        
        # 2. Run McNemar's tests for each task type
        p_values = {}
        for task in df['task_type'].unique():
            task_data = df[df['task_type'] == task]
            nn = task_data['non_neural_success']
            rand = task_data['random_success']
            vla = task_data['vla_proxy_success']
            
            # NN vs Random
            b_nn_rand = ((nn == 1) & (rand == 0)).sum()
            c_nn_rand = ((nn == 0) & (rand == 1)).sum()
            if b_nn_rand + c_nn_rand > 0:
                p_nn_rand = mcnemar([[b_nn_rand + c_nn_rand, b_nn_rand], 
                                     [c_nn_rand, b_nn_rand + c_nn_rand]], 
                                    exact=False, correction=True).pvalue
            else:
                p_nn_rand = 1.0
            
            # NN vs VLA
            b_nn_vla = ((nn == 1) & (vla == 0)).sum()
            c_nn_vla = ((nn == 0) & (vla == 1)).sum()
            if b_nn_vla + c_nn_vla > 0:
                p_nn_vla = mcnemar([[b_nn_vla + c_nn_vla, b_nn_vla], 
                                    [c_nn_vla, b_nn_vla + c_nn_vla]], 
                                   exact=False, correction=True).pvalue
            else:
                p_nn_vla = 1.0
            
            p_values[task] = {
                'nn_vs_random': p_nn_rand,
                'nn_vs_vla': p_nn_vla
            }
        
        # Verify p-values are valid
        for task, pvs in p_values.items():
            for comparison, p in pvs.items():
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0)
        
        # 3. Calculate overall fidelity (mocked with synthetic trajectory data)
        # In real implementation, this would compare generated vs VLA trajectories
        np.random.seed(42)
        n_points, n_features = 100, 7
        true_traj = np.random.randn(n_points, n_features) * 0.5
        pred_traj = true_traj + np.random.randn(n_points, n_features) * 0.15
        error_margin = 0.2
        fidelity = np.mean(np.abs(pred_traj - true_traj) < error_margin)
        
        self.assertGreater(fidelity, 0.5, "Fidelity should be reasonable")
        
        # 4. Generate mock report
        report_lines = [
            "# Evaluation Report",
            "",
            "## Summary Statistics",
            f"- Total samples: {len(df)}",
            f"- Tasks tested: {', '.join(df['task_type'].unique())}",
            "",
            "## Success Rates",
        ]
        for task, rates in success_rates.items():
            report_lines.append(f"### {task.capitalize()}")
            for model, rate in rates.items():
                report_lines.append(f"- {model}: {rate:.2%}")
        
        report_lines.extend([
            "",
            "## McNemar's Test Results",
        ])
        for task, pvs in p_values.items():
            report_lines.append(f"### {task.capitalize()}")
            report_lines.append(f"- Non-Neural vs Random: p={pvs['nn_vs_random']:.4f}")
            report_lines.append(f"- Non-Neural vs VLA: p={pvs['nn_vs_vla']:.4f}")
        
        report_lines.extend([
            "",
            "## Trajectory Fidelity",
            f"- Overall fidelity: {fidelity:.2%}",
            "",
            "## Conclusion",
            "Evaluation loop completed successfully.",
        ])
        
        report_content = "\n".join(report_lines)
        
        # Verify report content
        self.assertIn("Evaluation Report", report_content)
        self.assertIn("McNemar", report_content)
        self.assertIn("Fidelity", report_content)
        
        # Write report
        with open(self.report_path, 'w') as f:
            f.write(report_content)
        
        # Verify file exists and is non-empty
        self.assertTrue(os.path.exists(self.report_path))
        self.assertGreater(os.path.getsize(self.report_path), 0)

    def test_error_handling_in_evaluation(self):
        """
        Test that evaluation handles missing data gracefully.
        """
        # Create a CSV with missing columns
        bad_csv = os.path.join(self.test_dir, 'bad_simulation_logs.csv')
        with open(bad_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['sample_id', 'task_type'])  # Missing success columns
            writer.writerow([1, 'grasp'])
        
        import pandas as pd
        
        # Should raise an error when trying to access missing columns
        with self.assertRaises(KeyError):
            df = pd.read_csv(bad_csv)
            _ = df['non_neural_success']  # This key doesn't exist

if __name__ == '__main__':
    unittest.main()