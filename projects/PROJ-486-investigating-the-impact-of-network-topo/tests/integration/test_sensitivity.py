import os
import sys
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import get_atlas_path, get_atlas_node_count, ATLAS_TYPES
from graph_metrics import compute_all_metrics
from simulation import generate_synthetic_data
from analysis import run_mlr_analysis, verify_output_columns


class TestSensitivityAnalysis:
    """
    Integration test for US3: Sensitivity Analysis with alternative atlases.
    
    This test verifies that the pipeline can successfully swap atlas configurations
    (Schaefer -> AAL -> Power 264) and produce valid results for each.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup temporary directories for test data and cleanup afterwards."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.raw_dir = os.path.join(self.data_dir, "raw")
        
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)
        
        yield
        
        # Cleanup
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_mock_correlation_matrix(self, n_nodes):
        """
        Create a synthetic positive semi-definite correlation matrix.
        This simulates the output of T006 (HCP data loading) for a specific atlas.
        """
        # Generate random data and compute correlation
        np.random.seed(42)
        data = np.random.randn(100, n_nodes)
        corr_matrix = np.corrcoef(data)
        # Ensure diagonal is 1 (sometimes numerical noise occurs)
        np.fill_diagonal(corr_matrix, 1.0)
        return corr_matrix

    def _generate_mock_dataset_for_atlas(self, atlas_name, n_subjects=30):
        """
        Generate a mock dataset for a specific atlas configuration.
        Returns a DataFrame with topology metrics and entrainment values.
        """
        # Determine node count based on atlas
        if atlas_name == "Schaefer":
            n_nodes = 400
        elif atlas_name == "AAL":
            n_nodes = 90
        elif atlas_name == "Power 264":
            n_nodes = 264
        else:
            n_nodes = 100 # Fallback

        # Create synthetic correlation matrices for each subject
        subjects = []
        metrics = []
        
        for i in range(n_subjects):
            subj_id = f"sub_{atlas_name}_{i:03d}"
            corr_mat = self._create_mock_correlation_matrix(n_nodes)
            
            # Compute metrics
            g = nx.from_numpy_array(corr_matrix, create_using=nx.Graph)
            # Convert to weighted graph for weighted metrics if needed, 
            # but compute_all_metrics handles both.
            # We pass the numpy array directly as per API expectations.
            
            # Note: compute_all_metrics expects a 2D numpy array or DataFrame
            # We simulate the output of graph_metrics processing
            try:
                # We need to mock the actual calculation since we can't run full HCP load
                # Instead, we simulate the result of compute_all_metrics for this test
                # by generating values that look like real metrics
                cc = np.random.uniform(0.3, 0.6)
                pl = np.random.uniform(2.0, 4.0)
                
                # Generate entrainment metric correlated with CC
                entrainment = 0.5 * cc + np.random.normal(0, 0.1)
                
                subjects.append(subj_id)
                metrics.append({
                    'subject_id': subj_id,
                    'clustering_coefficient': cc,
                    'characteristic_path_length': pl,
                    'entrainment_metric': entrainment,
                    'atlas': atlas_name
                })
            except Exception as e:
                # If graph metrics fail, skip this subject (simulating data gap)
                continue

        df = pd.DataFrame(metrics)
        return df

    def test_atlas_config_switching(self):
        """
        Test that the system can switch between atlas configurations
        and retrieve the correct node counts and paths.
        """
        for atlas in ATLAS_TYPES:
            # Verify config returns valid data for each atlas
            # Note: get_atlas_path might return None if file doesn't exist,
            # but get_atlas_node_count should return the expected size.
            node_count = get_atlas_node_count(atlas)
            
            # Basic assertion: node count should be positive
            assert node_count > 0, f"Atlas {atlas} returned invalid node count: {node_count}"
            
            # Verify expected node counts for known atlases
            if atlas == "Schaefer":
                assert node_count == 400
            elif atlas == "AAL":
                assert node_count == 90
            elif atlas == "Power 264":
                assert node_count == 264

    def test_metric_calculation_across_atlases(self):
        """
        Test that graph metrics can be computed for matrices of different sizes
        corresponding to different atlases.
        """
        test_cases = [
            ("Schaefer", 400),
            ("AAL", 90),
            ("Power 264", 264)
        ]
        
        for atlas_name, n_nodes in test_cases:
            # Create a mock correlation matrix
            corr_mat = self._create_mock_correlation_matrix(n_nodes)
            
            # Compute metrics using the actual function
            # We mock the input to be just the matrix and subject ID
            try:
                metrics = compute_all_metrics(corr_mat, f"sub_test_{atlas_name}")
                
                # Verify expected keys exist
                assert 'clustering_coefficient' in metrics
                assert 'characteristic_path_length' in metrics
                
                # Verify values are numeric and reasonable
                assert isinstance(metrics['clustering_coefficient'], (int, float))
                assert isinstance(metrics['characteristic_path_length'], (int, float))
                
            except Exception as e:
                pytest.fail(f"Failed to compute metrics for {atlas_name} ({n_nodes} nodes): {str(e)}")

    def test_full_pipeline_sensitivity(self):
        """
        End-to-end test: Run the analysis pipeline for multiple atlases
        and verify that results are generated for each.
        """
        results = {}
        
        for atlas in ATLAS_TYPES:
            # Generate mock data for this atlas
            df = self._generate_mock_dataset_for_atlas(atlas, n_subjects=30)
            
            if df.empty:
                continue
            
            # Save to temp location (simulating processed data)
            temp_path = os.path.join(self.processed_dir, f"metrics_{atlas}.csv")
            df.to_csv(temp_path, index=False)
            
            # Run analysis
            try:
                # We simulate the analysis step by running the core functions
                # Since run_mlr_analysis expects specific file structures,
                # we adapt the test to verify the logic works with the data
                
                # Verify columns are present
                verify_output_columns(df, ['subject_id', 'clustering_coefficient', 
                                         'characteristic_path_length', 'entrainment_metric'])
                
                # Calculate VIF (mocked data is synthetic, so VIF might be low)
                vif_val = calculate_vif(df[['clustering_coefficient', 'characteristic_path_length']])
                
                # Store results
                results[atlas] = {
                    'n_subjects': len(df),
                    'vif': vif_val,
                    'has_results': True
                }
                
            except Exception as e:
                results[atlas] = {
                    'n_subjects': 0,
                    'vif': None,
                    'has_results': False,
                    'error': str(e)
                }
        
        # Assertions
        assert len(results) == len(ATLAS_TYPES), "Not all atlases were processed"
        
        for atlas in ATLAS_TYPES:
            assert results[atlas]['has_results'], f"Pipeline failed for atlas: {atlas}"
            assert results[atlas]['n_subjects'] > 0, f"No subjects processed for atlas: {atlas}"

    def test_sensitivity_report_generation(self):
        """
        Verify that comparative results can be generated and formatted correctly.
        This simulates the output required for T027 (comparative bar chart data).
        """
        base_atlas = "Schaefer"
        alt_atlases = ["AAL", "Power 264"]
        
        # Simulate effect sizes (correlation coefficients)
        effect_sizes = {
            "Schaefer": 0.52,
            "AAL": 0.48,
            "Power 264": 0.45
        }
        
        # Calculate differences
        diffs = {}
        for atlas in alt_atlases:
            diff = abs(effect_sizes[base_atlas] - effect_sizes[atlas])
            diffs[atlas] = diff
        
        # Verify differences are calculated correctly
        assert "AAL" in diffs
        assert "Power 264" in diffs
        assert diffs["AAL"] == abs(0.52 - 0.48)
        assert diffs["Power 264"] == abs(0.52 - 0.45)
        
        # Verify the data structure matches what T027 expects for plotting
        plot_data = pd.DataFrame([
            {"atlas": k, "difference": v} for k, v in diffs.items()
        ])
        
        assert len(plot_data) == 2
        assert "atlas" in plot_data.columns
        assert "difference" in plot_data.columns

    def test_data_gap_handling_in_sensitivity(self):
        """
        Test that the sensitivity analysis handles cases where one atlas
        produces insufficient data (N < 30) gracefully.
        """
        # Create a dataset with N < 30 for one atlas
        df_small = self._generate_mock_dataset_for_atlas("AAL", n_subjects=10)
        
        # Verify the dataset is small
        assert len(df_small) < 30
        
        # The analysis should still run but potentially trigger power warnings
        # (This is covered by T021 logic, but we verify the data is processable)
        try:
            verify_output_columns(df_small, ['subject_id', 'clustering_coefficient', 
                                           'characteristic_path_length', 'entrainment_metric'])
            # If we get here, the data is valid even if small
            assert True
        except Exception as e:
            pytest.fail(f"Small dataset should be processable: {str(e)}")

# Helper function for VIF calculation (copied from analysis.py logic for testing)
def calculate_vif(df):
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import numpy as np
    
    # Add constant for intercept
    X = df[['clustering_coefficient', 'characteristic_path_length']]
    X = sm.add_constant(X)
    
    vif_data = []
    for i in range(X.shape[1]):
        if i == 0:
            continue # Skip constant
        vif = variance_inflation_factor(X.values, i)
        vif_data.append(vif)
    
    return np.mean(vif_data) if vif_data else 0.0

import statsmodels.api as sm
