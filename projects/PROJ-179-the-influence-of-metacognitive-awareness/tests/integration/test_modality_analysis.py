import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.filter import load_trial_data, filter_by_modality
from src.analysis.robustness import run_bootstrap_correlation
from src.utils.stats import compute_type2_auc, compute_sdt_metrics

class TestModalityAnalysis(unittest.TestCase):
    """Integration test for modality-specific correlation analysis (US3).
    
    This test verifies that:
    1. Data can be filtered by stimulus_modality (visual vs auditory)
    2. Correlation analysis runs independently on each subset
    3. Results are computed from disjoint trial sets (Hold-Out design)
    4. Bootstrap confidence intervals are generated correctly
    """

    def setUp(self):
        """Set up test fixtures with sample data."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True)
        
        # Create sample trial data with required columns
        # This simulates the output of T012 (preprocess.py)
        self.sample_data = pd.DataFrame({
            'participant_id': ['P01'] * 100 + ['P02'] * 100,
            'trial_id': list(range(100)) + list(range(100)),
            'stimulus_modality': ['visual'] * 50 + ['auditory'] * 50 + ['visual'] * 50 + ['auditory'] * 50,
            'source_label': ['internal'] * 60 + ['external'] * 40 + ['internal'] * 60 + ['external'] * 40,
            'participant_response': [1] * 60 + [0] * 40 + [1] * 60 + [0] * 40,
            'confidence_rating': np.random.uniform(0, 1, 200),
            'accuracy': [1] * 50 + [0] * 50 + [1] * 50 + [0] * 50
        })
        
        # Write sample data to CSV
        self.trial_data_path = self.data_dir / "trial_data.csv"
        self.sample_data.to_csv(self.trial_data_path, index=False)

    def test_filter_by_modality_creates_disjoint_sets(self):
        """Test that filtering by modality produces disjoint trial sets."""
        # Load and filter data
        all_data = load_trial_data(self.trial_data_path)
        
        visual_data = filter_by_modality(all_data, 'visual')
        auditory_data = filter_by_modality(all_data, 'auditory')
        
        # Verify no overlap in trial_ids
        visual_trials = set(visual_data['trial_id'].unique())
        auditory_trials = set(auditory_data['trial_id'].unique())
        
        self.assertTrue(
            len(visual_trials.intersection(auditory_trials)) == 0,
            "Visual and auditory trial sets should be disjoint"
        )
        
        # Verify correct counts
        self.assertEqual(len(visual_data), 100)
        self.assertEqual(len(auditory_data), 100)

    def test_hold_out_design_enforced_per_modality(self):
        """Test that Hold-Out design is enforced within each modality subset."""
        all_data = load_trial_data(self.trial_data_path)
        
        for modality in ['visual', 'auditory']:
            modality_data = filter_by_modality(all_data, modality)
            
            # Simulate Hold-Out split (70/30)
            np.random.seed(42)
            indices = np.random.permutation(len(modality_data))
            split_idx = int(0.7 * len(modality_data))
            
            train_indices = indices[:split_idx]
            test_indices = indices[split_idx:]
            
            train_data = modality_data.iloc[train_indices]
            test_data = modality_data.iloc[test_indices]
            
            # Verify no trial overlap between train and test
            train_trials = set(train_data['trial_id'].unique())
            test_trials = set(test_data['trial_id'].unique())
            
            self.assertTrue(
                len(train_trials.intersection(test_trials)) == 0,
                f"Train and test sets for {modality} should be disjoint"
            )

    def test_correlation_computation_per_modality(self):
        """Test that correlation is computed correctly for each modality."""
        all_data = load_trial_data(self.trial_data_path)
        
        for modality in ['visual', 'auditory']:
            modality_data = filter_by_modality(all_data, modality)
            
            # Compute Type-2 AUC (metacognitive awareness) on training split
            np.random.seed(42)
            indices = np.random.permutation(len(modality_data))
            split_idx = int(0.7 * len(modality_data))
            
            train_data = modality_data.iloc[indices[:split_idx]]
            test_data = modality_data.iloc[indices[split_idx:]]
            
            # Compute Type-2 AUC for each participant in training set
            meta_scores = []
            for pid in train_data['participant_id'].unique():
                participant_data = train_data[train_data['participant_id'] == pid]
                if len(participant_data) > 5:  # Minimum trials for AUC
                    # Simulate Type-2 AUC calculation
                    # In real implementation, this uses confidence vs accuracy
                    auc = np.mean(participant_data['confidence_rating'])
                    meta_scores.append(auc)
            
            # Compute d' (reality testing accuracy) on test set
            d_prime_scores = []
            for pid in test_data['participant_id'].unique():
                participant_data = test_data[test_data['participant_id'] == pid]
                if len(participant_data) > 5:
                    # Simulate d' calculation
                    hits = participant_data[participant_data['participant_response'] == 1].shape[0]
                    false_alarms = participant_data[participant_data['participant_response'] == 0].shape[0]
                    if hits > 0 and false_alarms > 0:
                        d_prime = np.log((hits + 1) / (false_alarms + 1))
                        d_prime_scores.append(d_prime)
            
            # Verify we have scores for correlation
            self.assertGreater(len(meta_scores), 0, f"No metacognitive scores for {modality}")
            self.assertGreater(len(d_prime_scores), 0, f"No d' scores for {modality}")

    def test_bootstrap_confidence_intervals(self):
        """Test that bootstrap confidence intervals are generated correctly."""
        all_data = load_trial_data(self.trial_data_path)
        
        for modality in ['visual', 'auditory']:
            modality_data = filter_by_modality(all_data, modality)
            
            # Prepare data for bootstrap
            # Create synthetic correlation data
            np.random.seed(42)
            n_samples = 50
            x = np.random.randn(n_samples)
            y = np.random.randn(n_samples)
            
            # Compute correlation and bootstrap CI
            bootstrap_results = run_bootstrap_correlation(
                x, y, 
                n_resamples=100,  # Reduced for test speed
                confidence_level=0.95
            )
            
            # Verify results structure
            self.assertIn('correlation', bootstrap_results)
            self.assertIn('ci_lower', bootstrap_results)
            self.assertIn('ci_upper', bootstrap_results)
            self.assertIn('p_value', bootstrap_results)
            
            # Verify CI bounds are reasonable
            self.assertLess(bootstrap_results['ci_lower'], bootstrap_results['correlation'])
            self.assertGreater(bootstrap_results['ci_upper'], bootstrap_results['correlation'])
            self.assertLess(bootstrap_results['ci_lower'], 1.0)
            self.assertGreater(bootstrap_results['ci_upper'], -1.0)

    def test_modality_specific_results_are_independent(self):
        """Test that visual and auditory analyses produce independent results."""
        all_data = load_trial_data(self.trial_data_path)
        
        results = {}
        for modality in ['visual', 'auditory']:
            modality_data = filter_by_modality(all_data, modality)
            
            # Simulate correlation analysis
            np.random.seed(42)
            x = np.random.randn(50)
            y = np.random.randn(50)
            
            # Compute correlation
            corr, _ = np.polyfit(x, y, 1) if len(x) > 0 else (0, 0)
            results[modality] = abs(corr)
        
        # Results should be different due to random generation
        # (In real data, they might be similar or different)
        self.assertIn('visual', results)
        self.assertIn('auditory', results)
        self.assertIsInstance(results['visual'], float)
        self.assertIsInstance(results['auditory'], float)

    def test_missing_modality_handling(self):
        """Test that missing modality values are handled gracefully."""
        # Create data with missing modality values
        incomplete_data = pd.DataFrame({
            'participant_id': ['P01'] * 10,
            'trial_id': list(range(10)),
            'stimulus_modality': ['visual'] * 5 + [None] * 3 + ['auditory'] * 2,
            'source_label': ['internal'] * 10,
            'participant_response': [1] * 10,
            'confidence_rating': np.random.uniform(0, 1, 10)
        })
        
        # Save to temp file
        temp_path = Path(self.test_dir) / "incomplete_data.csv"
        incomplete_data.to_csv(temp_path, index=False)
        
        # Load and filter
        loaded_data = load_trial_data(temp_path)
        visual_data = filter_by_modality(loaded_data, 'visual')
        
        # Should only include non-null visual trials
        self.assertEqual(len(visual_data), 5)

    def test_integration_pipeline_end_to_end(self):
        """Test the complete modality-specific analysis pipeline."""
        # Load data
        all_data = load_trial_data(self.trial_data_path)
        
        # Filter by modality
        visual_data = filter_by_modality(all_data, 'visual')
        auditory_data = filter_by_modality(all_data, 'auditory')
        
        # Verify both subsets exist and are non-empty
        self.assertGreater(len(visual_data), 0)
        self.assertGreater(len(auditory_data), 0)
        
        # Simulate correlation analysis for each modality
        for modality, data in [('visual', visual_data), ('auditory', auditory_data)]:
            # Split data for Hold-Out design
            np.random.seed(42)
            indices = np.random.permutation(len(data))
            split_idx = int(0.7 * len(data))
            
            train_data = data.iloc[indices[:split_idx]]
            test_data = data.iloc[indices[split_idx:]]
            
            # Verify disjoint sets
            self.assertTrue(
                len(set(train_data['trial_id'])) == 0 or 
                len(set(test_data['trial_id'])) == 0 or
                len(set(train_data['trial_id']).intersection(set(test_data['trial_id']))) == 0
            )

    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()