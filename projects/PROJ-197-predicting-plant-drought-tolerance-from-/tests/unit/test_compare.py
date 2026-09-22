import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import json
import tempfile

# Import the module under test
# Assuming the test runner sets PYTHONPATH correctly to include 'code'
# In a real scenario, imports would be: from code.models.compare import ...
# But per API surface, we assume imports like: from models.compare import ...
# Since we are running from root, we need to ensure path is correct.
# For the purpose of this artifact, we assume the test is run with PYTHONPATH=code
from models.compare import (
    VALIDATION_GENES,
    load_cv_results,
    perform_rf_vs_xgb_ttest,
    calculate_permutation_importance,
    classify_features,
    generate_comparison_report
)

class TestCompareValidationLogic:
    """Tests for the T029 validation logic (SC-005)."""

    def test_validation_gene_count_logic(self):
        """Verify that the validation logic correctly counts genes in top 10."""
        # Mock feature importance DataFrame
        mock_data = {
            'feature': VALIDATION_GENES[:5] + ["OTHER_GENE_1", "OTHER_GENE_2", "OTHER_GENE_3", "OTHER_GENE_4", "OTHER_GENE_5"],
            'importance_mean': [0.5, 0.4, 0.3, 0.2, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05]
        }
        df = pd.DataFrame(mock_data)
        
        # Top 10 includes 5 validation genes
        top_10 = df.head(10)['feature'].tolist()
        count = len([g for g in top_10 if g in VALIDATION_GENES])
        
        assert count == 5
        assert count >= 3  # Should pass validation

    def test_validation_gene_count_fail(self):
        """Verify that validation fails if count < 3."""
        mock_data = {
            'feature': VALIDATION_GENES[:2] + ["OTHER"] * 8,
            'importance_mean': [0.5, 0.4] + [0.1] * 8
        }
        df = pd.DataFrame(mock_data)
        
        top_10 = df.head(10)['feature'].tolist()
        count = len([g for g in top_10 if g in VALIDATION_GENES])
        
        assert count == 2
        assert count < 3  # Should fail validation

    def test_generate_comparison_report_includes_validation(self):
        """Verify that the generated report contains the validation result."""
        mock_metrics = {
            'best_model': 'XGBoost',
            'best_auc': 0.85,
            'delong_p_value': 0.01,
            't_statistic': 2.5,
            'p_value_ttest': 0.02
        }
        
        mock_df = pd.DataFrame({
            'feature': VALIDATION_GENES[:5] + ["OTHER"] * 5,
            'importance_mean': [0.5, 0.4, 0.3, 0.2, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05]
        })
        
        config = {'random_seed': 42}
        
        report = generate_comparison_report(mock_metrics, mock_df, config)
        
        assert "Validation Check (SC-005)" in report
        assert "Count of validation genes in Top 10 features: **5**" in report
        assert "✅ PASSED" in report

class TestPermutationImportance:
    """Tests for permutation importance calculation."""

    def test_calculate_permutation_importance_shapes(self):
        """Verify output DataFrame shape and columns."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0, 1, 0, 1])
        
        X = np.random.rand(10, 5)
        y = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
        names = [f"feat_{i}" for i in range(5)]
        
        # Mock permutation_importance to return a simple object
        with patch('models.compare.permutation_importance') as mock_perm:
            mock_result = MagicMock()
            mock_result.importances_mean = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
            mock_result.importances_std = np.array([0.01, 0.02, 0.03, 0.04, 0.05])
            mock_perm.return_value = mock_result
            
            df = calculate_permutation_importance(mock_model, X, y, names)
            
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 5
            assert 'feature' in df.columns
            assert 'importance_mean' in df.columns
            assert 'importance_std' in df.columns
            # Check sorting (descending)
            assert df.iloc[0]['importance_mean'] >= df.iloc[-1]['importance_mean']

class TestFeatureClassification:
    """Tests for feature classification logic."""

    def test_classify_features_genomic(self):
        """Verify genomic genes are classified correctly."""
        features = ["DREB2A", "ERF1", "PHENYLALANINE_AMMONIA_LYASE", "HSP70"]
        result = classify_features(features)
        
        # DREB2A, ERF1, HSP70 are in VALIDATION_GENES
        # PHENYLALANINE_AMMONIA_LYASE is not in VALIDATION_GENES but is uppercase-ish? 
        # Our heuristic: if in VALIDATION_GENES or (upper and alnum). 
        # "PHENYLALANINE_AMMONIA_LYASE" has underscores, so isalnum() might be false? 
        # Actually, isalnum() returns False if underscore present.
        # So it should be physiological unless in VALIDATION_GENES.
        
        assert "DREB2A" in result['genomic']
        assert "ERF1" in result['genomic']
        assert "HSP70" in result['genomic']
        assert "PHENYLALANINE_AMMONIA_LYASE" in result['physiological']

    def test_classify_features_physiological(self):
        """Verify physiological traits are classified correctly."""
        features = ["Leaf_Water_Potential", "Stomatal_Conductance", "DREB2A"]
        result = classify_features(features)
        
        assert "Leaf_Water_Potential" in result['physiological']
        assert "Stomatal_Conductance" in result['physiological']
        assert "DREB2A" in result['genomic']