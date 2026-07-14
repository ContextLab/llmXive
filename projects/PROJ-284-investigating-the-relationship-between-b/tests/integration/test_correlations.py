import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correlations import (
    load_metrics_data, 
    perform_pca_on_metrics, 
    generate_full_metrics_dataframe,
    calculate_correlation_with_covariate,
    apply_fdr_correction,
    main
)

class TestCorrelationWithSyntheticData:
    """
    Integration test for T023a and T023b.
    Verifies that PCA and metric merging work correctly on synthetic data.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories and files for the test."""
        self.tmp_path = tmp_path
        self.processed_dir = self.tmp_path / "processed"
        self.analysis_dir = self.tmp_path / "analysis"
        self.processed_dir.mkdir(parents=True)
        self.analysis_dir.mkdir(parents=True)

        # Create a synthetic aggregated_metrics.csv
        # T021/T022 output format
        data = {
            'subject_id': [f'sub-{i:03d}' for i in range(1, 11)],
            'modularity': np.random.rand(10) * 0.5 + 0.2,
            'global_efficiency': np.random.rand(10) * 0.3 + 0.4,
            'participation_coef': np.random.rand(10) * 0.2 + 0.1,
            'within_module_degree': np.random.rand(10) * 0.5 + 0.3,
            'mean_fd': np.random.rand(10) * 0.1
        }
        self.synthetic_df = pd.DataFrame(data)
        self.metrics_file = self.processed_dir / "aggregated_metrics.csv"
        self.synthetic_df.to_csv(self.metrics_file, index=False)

        # Patch the global paths in the module to use temp paths
        # We do this by monkey-patching the module's constants or passing them.
        # Since the functions use global constants, we need to be careful.
        # For this test, we will re-implement the logic locally or patch the constants.
        
        # Better approach: Override the constants in the module for the test duration
        import code.analysis.correlations as corr_mod
        self.original_processed = corr_mod.PROCESSED_DIR
        self.original_analysis = corr_mod.ANALYSIS_DIR
        self.original_agg_file = corr_mod.AGGREGATED_METRICS_FILE
        self.original_full_file = corr_mod.FULL_METRICS_FILE
        self.original_pca_loadings = corr_mod.PCA_LOADINGS_FILE
        self.original_factor_scores = corr_mod.FACTOR_SCORES_FILE

        corr_mod.PROCESSED_DIR = self.processed_dir
        corr_mod.ANALYSIS_DIR = self.analysis_dir
        corr_mod.AGGREGATED_METRICS_FILE = self.metrics_file
        corr_mod.FULL_METRICS_FILE = self.analysis_dir / "full_metrics.csv"
        corr_mod.PCA_LOADINGS_FILE = self.analysis_dir / "pca_loadings.csv"
        corr_mod.FACTOR_SCORES_FILE = self.analysis_dir / "factor_scores.csv"

        yield

        # Restore
        corr_mod.PROCESSED_DIR = self.original_processed
        corr_mod.ANALYSIS_DIR = self.original_analysis
        corr_mod.AGGREGATED_METRICS_FILE = self.original_agg_file
        corr_mod.FULL_METRICS_FILE = self.original_full_file
        corr_mod.PCA_LOADINGS_FILE = self.original_pca_loadings
        corr_mod.FACTOR_SCORES_FILE = self.original_factor_scores

    def test_pca_and_merge_workflow(self):
        """
        Test the full workflow: Load -> PCA -> Merge -> Save.
        Verifies that r, p, and q values (for correlation) are computed correctly 
        in a synthetic scenario (though this test focuses on structure and file existence).
        """
        # Run the main logic
        main()

        # Verify files exist
        assert self.analysis_dir.exists()
        assert (self.analysis_dir / "pca_loadings.csv").exists()
        assert (self.analysis_dir / "factor_scores.csv").exists()
        assert (self.analysis_dir / "full_metrics.csv").exists()

        # Load and verify content
        full_metrics = pd.read_csv(self.analysis_dir / "full_metrics.csv")
        
        # Check required columns
        required_cols = ['subject_id', 'modularity', 'global_efficiency', 'participation_coef', 
                         'within_module_degree', 'mean_fd', 'pca_factor_1', 'pca_factor_2']
        for col in required_cols:
            assert col in full_metrics.columns, f"Missing column: {col}"

        # Verify data integrity
        assert len(full_metrics) == 10
        assert not full_metrics['pca_factor_1'].isna().any()
        assert not full_metrics['pca_factor_2'].isna().any()

        # Test correlation function on synthetic data (T024 dependency check)
        # Create synthetic correlation data
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 5, 4, 5])
        r, p = calculate_correlation_with_covariate(x, y)
        
        # Known: strong positive correlation
        assert r > 0.5, f"Expected r > 0.5, got {r}"
        assert p < 0.1, f"Expected p < 0.1, got {p}"

        # Test FDR correction
        p_vals = [0.01, 0.05, 0.1, 0.2, 0.5]
        q_vals = apply_fdr_correction(p_vals)
        assert len(q_vals) == len(p_vals)
        # FDR values should be >= raw p-values (monotonicity)
        for p, q in zip(p_vals, q_vals):
            assert q >= p, f"FDR q-value {q} should be >= p-value {p}"
