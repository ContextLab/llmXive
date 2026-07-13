"""
T025: Integration test for modality-specific correlation analysis.

Tests that filtering the dataset by modality produces separate 
correlation coefficients with CIs.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.robustness import load_filtered_data, compute_hold_out_metrics_for_modality
from src.analysis.filter import filter_by_modality

class TestModalityAnalysis(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.trial_data_path = Path(self.temp_dir) / "trial_data.csv"
        
        # Create sample trial data with both modalities
        data = {
            'participant_id': [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'trial_id': [1, 2, 3, 1, 2, 3, 1, 2, 3],
            'stimulus_modality': ['visual', 'visual', 'auditory', 'visual', 'auditory', 'auditory', 'visual', 'visual', 'auditory'],
            'source_label': ['real', 'fake', 'real', 'real', 'fake', 'real', 'fake', 'real', 'real'],
            'participant_response': ['real', 'fake', 'real', 'real', 'fake', 'real', 'fake', 'real', 'real'],
            'confidence_rating': [0.8, 0.3, 0.9, 0.7, 0.2, 0.8, 0.4, 0.9, 0.85]
        }
        
        df = pd.DataFrame(data)
        df.to_csv(self.trial_data_path, index=False)
        
        # Update path for testing
        import src.analysis.robustness as robustness_module
        original_load = robustness_module.load_filtered_data
        def mock_load(modality):
            df = pd.read_csv(self.trial_data_path)
            return df[df['stimulus_modality'] == modality]
        robustness_module.load_filtered_data = mock_load

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filter_by_modality(self):
        """Test that data can be filtered by modality."""
        # Filter visual
        visual_data = load_filtered_data('visual')
        self.assertEqual(len(visual_data), 5)  # 5 visual trials
        
        # Filter auditory
        auditory_data = load_filtered_data('auditory')
        self.assertEqual(len(auditory_data), 4)  # 4 auditory trials

    def test_modality_specific_correlation(self):
        """Test that correlation can be computed for each modality."""
        # Visual modality
        visual_results = compute_hold_out_metrics_for_modality('visual')
        self.assertIn('status', visual_results)
        
        # Auditory modality
        auditory_results = compute_hold_out_metrics_for_modality('auditory')
        self.assertIn('status', auditory_results)

    def test_separate_correlation_coefficients(self):
        """Test that separate correlation coefficients are produced."""
        visual_results = compute_hold_out_metrics_for_modality('visual')
        auditory_results = compute_hold_out_metrics_for_modality('auditory')
        
        # Both should have correlation values (or NaN if insufficient data)
        self.assertIn('correlation', visual_results)
        self.assertIn('correlation', auditory_results)
        
        # Values should be different (or both NaN)
        if not (np.isnan(visual_results.get('correlation', np.nan)) and 
                np.isnan(auditory_results.get('correlation', np.nan))):
            self.assertNotEqual(
                visual_results.get('correlation'),
                auditory_results.get('correlation')
            )

    def test_confidence_intervals(self):
        """Test that confidence intervals are computed for each modality."""
        visual_results = compute_hold_out_metrics_for_modality('visual')
        auditory_results = compute_hold_out_metrics_for_modality('auditory')
        
        # Check for CI fields
        self.assertIn('ci_lower', visual_results)
        self.assertIn('ci_upper', visual_results)
        self.assertIn('ci_lower', auditory_results)
        self.assertIn('ci_upper', auditory_results)

if __name__ == '__main__':
    unittest.main()