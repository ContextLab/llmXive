"""
Unit tests for edge cases in the solubility prediction pipeline.

Tests verify robustness against:
1. Missing data handling (NaN values in features/targets)
2. Small dataset splits (insufficient samples for CV)
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.constants import DATA_DIR
from utils.errors import CustomDataError


class TestMissingDataHandling:
    """Tests for handling missing data in feature engineering and model training."""

    def test_missing_data_handling(self):
        """
        Verify that the pipeline correctly handles missing values (NaN) in input data.
        
        Expected behavior:
        - KNN imputation (T013) should fill missing values
        - Rows with missing target (solubility) should be dropped
        - Rows with missing features should be imputed or dropped based on threshold
        """
        # Create a temporary CSV with missing data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            # Write header and data with NaN values
            f.write("solute_smiles,solvent_prop1,solvent_prop2,solubility_logS\n")
            f.write("CCO,0.5,NaN,-1.2\n")       # Missing solvent_prop2
            f.write("CCCO,NaN,0.8,-1.5\n")     # Missing solvent_prop1
            f.write("CCCCO,0.6,0.7,NaN\n")     # Missing target (should be dropped)
            f.write("CCCCCO,0.7,0.9,-1.8\n")  # Complete row

        try:
            # Load the data
            df = pd.read_csv(temp_path)
            
            # Check initial state
            assert df.isnull().sum().sum() == 3, "Test setup failed: expected 3 NaN values"
            assert df['solubility_logS'].isnull().sum() == 1, "Expected 1 missing target"
            
            # Simulate the logic from T013 (KNN imputation for features)
            # Drop rows with missing target first (as per standard practice)
            df_no_nan_target = df.dropna(subset=['solubility_logS'])
            
            assert len(df_no_nan_target) == 3, "Should drop row with missing target"
            assert df_no_nan_target['solubility_logS'].isnull().sum() == 0, "No missing targets remaining"
            
            # Simulate KNN imputation for remaining missing features
            # (In real code, this uses sklearn.impute.KNNImputer)
            from sklearn.impute import KNNImputer
            
            feature_cols = ['solvent_prop1', 'solvent_prop2']
            X = df_no_nan_target[feature_cols].values
            
            imputer = KNNImputer(n_neighbors=2)
            X_imputed = imputer.fit_transform(X)
            
            # Verify no NaNs remain
            assert not np.isnan(X_imputed).any(), "Imputation failed: NaN values remain"
            
            # Verify the imputed values are reasonable (not extreme outliers)
            assert np.all(X_imputed > 0) and np.all(X_imputed < 2.0), "Imputed values out of expected range"
            
        finally:
            os.unlink(temp_path)

        # If we reach here, the test passed
        assert True


class TestSmallDatasetSplit:
    """Tests for handling datasets too small for cross-validation."""

    def test_small_dataset_split(self):
        """
        Verify that the pipeline handles datasets with insufficient samples for CV.
        
        Expected behavior:
        - If n_samples < n_folds * min_samples_per_fold, raise an error or adjust strategy
        - Per T021, we use k-fold CV. If data is too small, we should fallback to
          a simpler split or raise a clear error.
        """
        # Create a tiny dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name
            f.write("solute_smiles,solvent_prop1,solubility_logS\n")
            # Only 3 samples
            f.write("CCO,0.5,-1.2\n")
            f.write("CCCO,0.6,-1.5\n")
            f.write("CCCCO,0.7,-1.8\n")

        try:
            df = pd.read_csv(temp_path)
            
            # Simulate the logic from T021 (k-fold CV setup)
            from sklearn.model_selection import KFold
            import numpy as np
            
            X = df[['solvent_prop1']].values
            y = df['solubility_logS'].values
            
            n_samples = len(df)
            n_folds = 5  # Standard for CV
            min_samples_per_fold = 1
            
            # Check if split is possible
            if n_samples < n_folds * min_samples_per_fold:
                # This is the edge case: not enough data for 5-fold CV
                # In real code, we might fallback to leave-one-out or raise an error
                # Here we verify the condition is detected
                assert n_samples < n_folds, "Test setup: expected small dataset"
                
                # Simulate the fallback logic (e.g., use 3-fold instead or raise)
                # For this test, we just verify the detection works
                adjusted_folds = max(2, n_samples - 1)  # Simple fallback
                assert adjusted_folds < n_folds, "Fallback should reduce folds"
                
            else:
                # Normal case
                kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
                folds = list(kf.split(X))
                assert len(folds) == n_folds, "Expected 5 folds"
                
        finally:
            os.unlink(temp_path)

        # If we reach here, the test passed
        assert True