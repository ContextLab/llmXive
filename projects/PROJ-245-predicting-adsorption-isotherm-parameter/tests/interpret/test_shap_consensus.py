import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interpret.shap_analysis import validate_consensus, retrain_top_features, run_shap_analysis_pipeline

class TestConsensusValidation:
    """Tests for SC-002 consensus validation logic."""

    def test_validate_consensus_with_perfect_match(self):
        """Test validation when all top features match consensus."""
        shap_results = {
            'feature_importance': {
                'polarizability': 0.4,
                'kinetic_diameter': 0.3,
                'molecular_volume': 0.2,
                'other_feature': 0.1
            }
        }
        
        result = validate_consensus(shap_results)
        
        assert result['status'] == 'success'
        assert result['match_count'] == 3
        assert result['sc002_satisfied'] == True
        assert len(result['matched_features']) == 3
        
        # Check top 3 matches
        top_3_matched = [m for m in result['matched_features'] if m['rank'] <= 3]
        assert len(top_3_matched) >= 2  # SC-002 requirement

    def test_validate_consensus_with_partial_match(self):
        """Test validation when only some features match consensus."""
        shap_results = {
            'feature_importance': {
                'polarizability': 0.5,
                'unknown_feature': 0.3,
                'another_unknown': 0.2
            }
        }
        
        result = validate_consensus(shap_results)
        
        assert result['status'] == 'success'
        assert result['match_count'] == 1
        assert result['sc002_satisfied'] == False  # Only 1 match in top 3

    def test_validate_consensus_with_case_insensitive_matching(self):
        """Test that feature names are matched case-insensitively."""
        shap_results = {
            'feature_importance': {
                'POLARIZABILITY': 0.5,
                'Kinetic_Diameter': 0.3,
                'molecular_volume': 0.2
            }
        }
        
        result = validate_consensus(shap_results)
        
        assert result['match_count'] == 3
        assert result['sc002_satisfied'] == True

    def test_validate_consensus_handles_missing_data(self):
        """Test validation with invalid input."""
        result = validate_consensus(None)
        assert result['status'] == 'error'
        
        result = validate_consensus({})
        assert result['status'] == 'error'

class TestRetrainTopFeatures:
    """Tests for SC-003 retraining logic."""

    def test_retrain_top_features_satisfies_sc003(self):
        """Test that retraining on top features can satisfy SC-003."""
        # Create synthetic data with clear relationships
        np.random.seed(42)
        n_samples = 200
        
        X = pd.DataFrame({
            'polarizability': np.random.rand(n_samples),
            'kinetic_diameter': np.random.rand(n_samples),
            'molecular_volume': np.random.rand(n_samples),
            'noise_feature': np.random.rand(n_samples)
        })
        
        # Create target with strong dependence on top 3 features
        y = (
            2.0 * X['polarizability'] +
            1.5 * X['kinetic_diameter'] +
            1.0 * X['molecular_volume'] +
            0.1 * np.random.rand(n_samples)  # small noise
        )
        
        result = retrain_top_features(X, y, top_n=3)
        
        assert result['status'] == 'success'
        assert result['top_n'] == 3
        assert len(result['selected_features']) == 3
        assert result['sc003_satisfied'] == True  # R² >= 0.60

    def test_retrain_top_features_fails_sc003_with_weak_signal(self):
        """Test that retraining fails SC-003 when signal is weak."""
        np.random.seed(42)
        n_samples = 200
        
        X = pd.DataFrame({
            'feature1': np.random.rand(n_samples),
            'feature2': np.random.rand(n_samples),
            'feature3': np.random.rand(n_samples),
            'feature4': np.random.rand(n_samples)
        })
        
        # Target is mostly noise
        y = 0.1 * X['feature1'] + 0.05 * np.random.rand(n_samples)
        
        result = retrain_top_features(X, y, top_n=3)
        
        assert result['status'] == 'success'
        assert result['sc003_satisfied'] == False  # R² < 0.60

class TestFullPipeline:
    """Integration tests for the full SHAP analysis pipeline."""

    def test_run_shap_analysis_pipeline_creates_reports(self):
        """Test that the pipeline creates the required report files."""
        # Create dummy data
        shap_results = {
            'feature_importance': {
                'polarizability': 0.4,
                'kinetic_diameter': 0.3,
                'molecular_volume': 0.2,
                'other': 0.1
            }
        }
        
        X_train = pd.DataFrame({
            'polarizability': np.random.rand(50),
            'kinetic_diameter': np.random.rand(50),
            'molecular_volume': np.random.rand(50)
        })
        y_train = pd.Series(np.random.rand(50))
        
        # Run pipeline
        results = run_shap_analysis_pipeline(
            shap_results=shap_results,
            X_train=X_train,
            y_train=y_train
        )
        
        # Verify reports were created
        sc002_path = Path('data/validation/sc002_match_report.json')
        sc003_path = Path('data/validation/sc003_r2_report.json')
        
        assert sc002_path.exists(), "SC-002 report not created"
        assert sc003_path.exists(), "SC-003 report not created"
        
        # Verify report contents
        with open(sc002_path) as f:
            sc002_data = json.load(f)
        assert sc002_data['status'] == 'success'
        assert 'sc002_satisfied' in sc002_data
        
        with open(sc003_path) as f:
            sc003_data = json.load(f)
        assert sc003_data['status'] == 'success'
        assert 'sc003_satisfied' in sc003_data
        
        # Cleanup
        sc002_path.unlink()
        sc003_path.unlink()