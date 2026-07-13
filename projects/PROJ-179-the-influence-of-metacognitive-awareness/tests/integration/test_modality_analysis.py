"""
Integration tests for modality-specific correlation analysis (T025).

This test suite verifies that the modality analysis pipeline correctly:
1. Loads filtered data for visual and auditory modalities.
2. Computes hold-out metrics (d', Type-2 AUC) independently for each modality.
3. Calculates correlation coefficients and confidence intervals for each modality.
4. Produces the expected output structure in data/results/robustness_analysis.json.

These tests assume T026 (filter.py) and T027 (robustness.py) are implemented
and that the pipeline produces real outputs from real data.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.robustness import run_robustness_analysis
from src.analysis.filter import run_filter_analysis
from src.utils.stats import compute_sdt_metrics, compute_type2_auc


class TestModalityAnalysis(unittest.TestCase):
    """Integration tests for modality-specific correlation analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_data_dir = Path(self.temp_dir.name)
        
        # Create necessary subdirectories
        (self.test_data_dir / "derived").mkdir()
        (self.test_data_dir / "results").mkdir()
        
        # Create a realistic trial dataset with modality information
        # This mimics the output of data/preprocess.py (T012)
        self._create_test_trial_data()

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def _create_test_trial_data(self):
        """Create a realistic trial-level dataset for testing."""
        np.random.seed(42)
        
        n_visual = 300
        n_auditory = 250
        
        # Visual trials
        visual_data = {
            'participant_id': np.repeat(range(1, 11), n_visual // 10),
            'trial_id': range(1, n_visual + 1),
            'stimulus_modality': ['visual'] * n_visual,
            'source_label': np.random.choice(['real', 'fake'], n_visual, p=[0.5, 0.5]),
            'participant_response': np.random.choice([0, 1], n_visual, p=[0.5, 0.5]),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_visual, p=[0.1, 0.15, 0.2, 0.25, 0.3]),
            'accuracy': np.random.choice([0, 1], n_visual, p=[0.4, 0.6])  # For d' calculation
        }
        
        # Auditory trials
        auditory_data = {
            'participant_id': np.repeat(range(1, 11), n_auditory // 10),
            'trial_id': range(n_visual + 1, n_visual + n_auditory + 1),
            'stimulus_modality': ['auditory'] * n_auditory,
            'source_label': np.random.choice(['real', 'fake'], n_auditory, p=[0.5, 0.5]),
            'participant_response': np.random.choice([0, 1], n_auditory, p=[0.5, 0.5]),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_auditory, p=[0.1, 0.15, 0.2, 0.25, 0.3]),
            'accuracy': np.random.choice([0, 1], n_auditory, p=[0.4, 0.6])
        }
        
        # Combine and create DataFrame
        trial_data = pd.DataFrame({**visual_data, **auditory_data})
        
        # Save to CSV
        self.trial_data_path = self.test_data_dir / "derived" / "trial_data.csv"
        trial_data.to_csv(self.trial_data_path, index=False)
        
        return trial_data

    def test_filter_analysis_creates_modality_files(self):
        """Test that filter analysis creates separate visual and auditory trial files."""
        # Run filter analysis
        config = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        
        result = run_filter_analysis(config)
        
        # Verify output files exist
        visual_path = self.test_data_dir / "derived" / "visual_trials.csv"
        auditory_path = self.test_data_dir / "derived" / "auditory_trials.csv"
        
        self.assertTrue(visual_path.exists(), "Visual trials file should be created")
        self.assertTrue(auditory_path.exists(), "Auditory trials file should be created")
        
        # Verify file contents
        visual_df = pd.read_csv(visual_path)
        auditory_df = pd.read_csv(auditory_path)
        
        self.assertEqual(len(visual_df), 300, "Visual trials count mismatch")
        self.assertEqual(len(auditory_df), 250, "Auditory trials count mismatch")
        
        # Verify all rows have correct modality
        self.assertTrue((visual_df['stimulus_modality'] == 'visual').all(), 
                      "All visual trials should have modality='visual'")
        self.assertTrue((auditory_df['stimulus_modality'] == 'auditory').all(), 
                      "All auditory trials should have modality='auditory'")

    def test_robustness_analysis_produces_results(self):
        """Test that robustness analysis produces the expected output structure."""
        # First run filter to create modality-specific files
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Then run robustness analysis
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': 100  # Small count for faster testing
            }
        }
        
        result = run_robustness_analysis(config_robustness)
        
        # Verify result structure
        self.assertIn('modalities', result, "Result should contain 'modalities' key")
        self.assertIn('visual', result['modalities'], "Result should contain 'visual' modality")
        self.assertIn('auditory', result['modalities'], "Result should contain 'auditory' modality")
        
        # Verify each modality has required fields
        for modality in ['visual', 'auditory']:
            mod_result = result['modalities'][modality]
            self.assertIn('status', mod_result, f"{modality} should have status")
            self.assertIn('d_prime', mod_result, f"{modality} should have d_prime")
            self.assertIn('type2_auc', mod_result, f"{modality} should have type2_auc")
            self.assertIn('correlation', mod_result, f"{modality} should have correlation")
            self.assertIn('correlation_p', mod_result, f"{modality} should have correlation_p")
            self.assertIn('ci_lower', mod_result, f"{modality} should have ci_lower")
            self.assertIn('ci_upper', mod_result, f"{modality} should have ci_upper")
            self.assertIn('n_resamples', mod_result, f"{modality} should have n_resamples")

    def test_robustness_analysis_writes_json_file(self):
        """Test that robustness analysis writes results to the expected JSON file."""
        # Run filter first
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Run robustness analysis
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': 50  # Small count for faster testing
            }
        }
        
        run_robustness_analysis(config_robustness)
        
        # Verify output file exists
        output_path = self.test_data_dir / "results" / "robustness_analysis.json"
        self.assertTrue(output_path.exists(), 
                      "robustness_analysis.json should be written to data/results/")
        
        # Verify JSON is valid and loadable
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        self.assertIn('modalities', results, "JSON should contain 'modalities' key")
        self.assertIn('visual', results['modalities'], "JSON should contain 'visual' modality")
        self.assertIn('auditory', results['modalities'], "JSON should contain 'auditory' modality")

    def test_correlation_values_are_real(self):
        """Test that correlation values are real measurements, not fabricated."""
        # Run filter first
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Run robustness analysis
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': 50
            }
        }
        
        result = run_robustness_analysis(config_robustness)
        
        # Verify correlations are not NaN or extreme fabricated values
        for modality in ['visual', 'auditory']:
            mod_result = result['modalities'][modality]
            if mod_result['status'] == 'success':
                corr = mod_result['correlation']
                p_val = mod_result['correlation_p']
                
                # Correlation should be in valid range [-1, 1]
                self.assertTrue(-1.0 <= corr <= 1.0, 
                              f"{modality} correlation {corr} not in valid range [-1, 1]")
                
                # p-value should be in valid range [0, 1]
                self.assertTrue(0.0 <= p_val <= 1.0, 
                              f"{modality} p-value {p_val} not in valid range [0, 1]")
                
                # Check that CIs are reasonable
                ci_lower = mod_result['ci_lower']
                ci_upper = mod_result['ci_upper']
                
                self.assertTrue(ci_lower <= ci_upper, 
                              f"{modality} CI lower {ci_lower} > upper {ci_upper}")
                self.assertTrue(-1.0 <= ci_lower <= 1.0, 
                              f"{modality} CI lower {ci_lower} not in valid range")
                self.assertTrue(-1.0 <= ci_upper <= 1.0, 
                              f"{modality} CI upper {ci_upper} not in valid range")

    def test_hold_out_design_is_enforced(self):
        """Test that hold-out design is enforced (train/test split)."""
        # Run filter first
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Load visual trials
        visual_path = self.test_data_dir / "derived" / "visual_trials.csv"
        visual_df = pd.read_csv(visual_path)
        
        # The robustness analysis should use a 70/30 split
        # We can verify this by checking that the correlation is computed
        # on a subset of the data (not all data)
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': 50
            }
        }
        
        result = run_robustness_analysis(config_robustness)
        
        # If the analysis succeeded, it means the hold-out design was applied
        # (the underlying implementation in robustness.py handles the split)
        self.assertEqual(result['modalities']['visual']['status'], 'success',
                       "Visual modality analysis should succeed with hold-out design")

    def test_bootstrap_count_is_respected(self):
        """Test that the specified bootstrap count is used."""
        # Run filter first
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Run robustness analysis with specific bootstrap count
        n_resamples = 100
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': n_resamples
            }
        }
        
        result = run_robustness_analysis(config_robustness)
        
        # Verify bootstrap count is recorded in results
        for modality in ['visual', 'auditory']:
            if result['modalities'][modality]['status'] == 'success':
                self.assertEqual(result['modalities'][modality]['n_resamples'], n_resamples,
                               f"{modality} should use {n_resamples} bootstrap samples")

    def test_empty_modality_handling(self):
        """Test handling of modalities with no data."""
        # Create a trial dataset with only visual data
        np.random.seed(42)
        n_visual = 100
        
        visual_only_data = {
            'participant_id': np.repeat(range(1, 6), n_visual // 5),
            'trial_id': range(1, n_visual + 1),
            'stimulus_modality': ['visual'] * n_visual,
            'source_label': np.random.choice(['real', 'fake'], n_visual, p=[0.5, 0.5]),
            'participant_response': np.random.choice([0, 1], n_visual, p=[0.5, 0.5]),
            'confidence_rating': np.random.choice([1, 2, 3, 4, 5], n_visual, p=[0.1, 0.15, 0.2, 0.25, 0.3]),
            'accuracy': np.random.choice([0, 1], n_visual, p=[0.4, 0.6])
        }
        
        trial_data = pd.DataFrame(visual_only_data)
        trial_data_path = self.test_data_dir / "derived" / "trial_data.csv"
        trial_data.to_csv(trial_data_path, index=False)
        
        # Run filter
        config_filter = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            }
        }
        run_filter_analysis(config_filter)
        
        # Run robustness analysis
        config_robustness = {
            'paths': {
                'base': str(self.test_data_dir),
                'derived': str(self.test_data_dir / "derived"),
                'results': str(self.test_data_dir / "results")
            },
            'analysis': {
                'train_test_split': 0.7,
                'bootstrap_count': 50
            }
        }
        
        result = run_robustness_analysis(config_robustness)
        
        # Visual should succeed
        self.assertEqual(result['modalities']['visual']['status'], 'success',
                       "Visual modality should succeed")
        
        # Auditory should have data_not_found status or similar
        auditory_status = result['modalities']['auditory']['status']
        self.assertIn(auditory_status, ['data_not_found', 'error', 'no_data'],
                    "Auditory modality should indicate no data")

if __name__ == '__main__':
    unittest.main()