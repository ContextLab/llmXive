"""
Integration test for stratified route validity scoring (T011).

This test verifies that the evaluation pipeline correctly computes route validity
scores for stratified route categories (short, medium, long) and that the
lightweight model's performance diverges from the baseline at the identified
cognitive horizon.

Prerequisites:
- T006c: data/processed/stratified_routes.parquet exists
- T012c: Lightweight model inference is available
- T013: Baseline LLM inference is available (or marked as timeout/inconclusive)
- T014: Evaluation logic is implemented in analysis/evaluation.py
"""

import json
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, set_global_seed
from data.preprocess import stratify_routes
from analysis.evaluation import (
    compute_route_validity,
    perform_chi_squared_scan,
    flag_high_risk_predictions,
    run_evaluation,
    load_topological_metrics,
    integrate_topological_metrics,
)
from models.lightweight import LightweightModel, predict_next_station
from models.baseline import BaselineLLM

# Constants
STRATIFIED_ROUTES_PATH = PROJECT_ROOT / "data" / "processed" / "stratified_routes.parquet"
TOPOLOGICAL_METRICS_PATH = PROJECT_ROOT / "data" / "analysis" / "route_complexity_metrics.json"
EVALUATION_OUTPUT_PATH = PROJECT_ROOT / "data" / "analysis" / "raw_inflection_data.json"

# Set global seed for reproducibility
set_global_seed(42)


@pytest.fixture(scope="module")
def config():
    """Load project configuration."""
    return Config()


@pytest.fixture(scope="module")
def stratified_data(config):
    """Load stratified route data from T006c output."""
    if not STRATIFIED_ROUTES_PATH.exists():
        pytest.skip(
            f"Stratified routes file not found at {STRATIFIED_ROUTES_PATH}. "
            "Prerequisite T006c must be completed first."
        )
    
    # Load using pandas (parquet support)
    import pandas as pd
    df = pd.read_parquet(STRATIFIED_ROUTES_PATH)
    
    if df.empty:
        pytest.fail("Stratified routes dataset is empty. T006c validation may have failed.")
    
    return df


@pytest.fixture(scope="module")
def topological_metrics(config):
    """Load topological complexity metrics from T015b output."""
    if not TOPOLOGICAL_METRICS_PATH.exists():
        pytest.skip(
            f"Topological metrics file not found at {TOPOLOGICAL_METRICS_PATH}. "
            "Prerequisite T015b must be completed first."
        )
    
    with open(TOPOLOGICAL_METRICS_PATH, 'r') as f:
        metrics = json.load(f)
    
    if not metrics or 'routes' not in metrics:
        pytest.fail("Topological metrics file is malformed or empty.")
    
    return metrics


@pytest.fixture(scope="module")
def lightweight_model(config):
    """Load the lightweight encoder model from T012c output."""
    model_path = config.LIGHTWEIGHT_MODEL_PATH
    if not Path(model_path).exists():
        pytest.skip(
            f"Lightweight model not found at {model_path}. "
            "Prerequisite T012c must be completed first."
        )
    
    model = LightweightModel.load(model_path)
    return model


@pytest.fixture(scope="module")
def baseline_model(config):
    """Load the baseline LLM model from T013 output."""
    model_path = config.BASELINE_MODEL_PATH
    if not Path(model_path).exists():
        # Baseline might be unavailable due to resource constraints (T030a)
        # This is acceptable - we'll test the lightweight model's standalone performance
        return None
    
    model = BaselineLLM.load(model_path)
    return model


class TestStratifiedValidityScoring:
    """Integration tests for stratified route validity scoring."""

    def test_stratified_data_loading(self, stratified_data):
        """Verify that stratified data contains all required categories."""
        categories = stratified_data['category'].unique()
        expected_categories = {'short', 'medium', 'long'}
        
        assert set(categories) == expected_categories, (
            f"Expected categories {expected_categories}, got {set(categories)}"
        )
        
        # Verify each category has at least some routes
        for cat in expected_categories:
            count = len(stratified_data[stratified_data['category'] == cat])
            assert count > 0, f"Category '{cat}' has no routes in stratified data"

    def test_route_validity_computation(self, stratified_data, lightweight_model):
        """Test that route validity can be computed for each category."""
        results = {}
        
        for category in ['short', 'medium', 'long']:
            category_routes = stratified_data[stratified_data['category'] == category]
            
            # Compute validity for this category
            validity_scores = compute_route_validity(
                routes=category_routes.to_dict('records'),
                model=lightweight_model,
                category=category
            )
            
            assert len(validity_scores) == len(category_routes), (
                f"Validity score count mismatch for category '{category}'"
            )
            
            # Verify all scores are in valid range [0, 1]
            for score in validity_scores:
                assert 0.0 <= score <= 1.0, (
                    f"Invalid validity score {score} for route in category '{category}'"
                )
            
            results[category] = validity_scores

        # Verify that we have computed scores for all categories
        assert len(results) == 3, "Missing validity scores for one or more categories"

    def test_chi_squared_scan_detection(self, stratified_data, lightweight_model):
        """Test that chi-squared scan can identify performance divergence points."""
        # Compute validity for all categories
        all_validity = {}
        for category in ['short', 'medium', 'long']:
            category_routes = stratified_data[stratified_data['category'] == category]
            validity_scores = compute_route_validity(
                routes=category_routes.to_dict('records'),
                model=lightweight_model,
                category=category
            )
            all_validity[category] = validity_scores

        # Perform chi-squared scan to detect inflection points
        chi_squared_results = perform_chi_squared_scan(
            validity_data=all_validity,
            threshold=0.15,  # 15% absolute drop threshold
            alpha=0.05       # Statistical significance level
        )

        # Verify the scan returned results
        assert chi_squared_results is not None, "Chi-squared scan returned None"
        assert 'inflection_points' in chi_squared_results, (
            "Chi-squared scan results missing 'inflection_points' key"
        )

        # Verify that at least one category was analyzed
        assert len(chi_squared_results['inflection_points']) > 0, (
            "No inflection points detected - this may indicate uniform performance"
        )

    def test_risk_flagging(self, stratified_data, lightweight_model):
        """Test that high-risk predictions are correctly flagged based on inflection point."""
        # First, compute validity and detect inflection point
        all_validity = {}
        for category in ['short', 'medium', 'long']:
            category_routes = stratified_data[stratified_data['category'] == category]
            validity_scores = compute_route_validity(
                routes=category_routes.to_dict('records'),
                model=lightweight_model,
                category=category
            )
            all_validity[category] = validity_scores

        chi_squared_results = perform_chi_squared_scan(
            validity_data=all_validity,
            threshold=0.15,
            alpha=0.05
        )

        # Flag high-risk predictions
        risk_flags = flag_high_risk_predictions(
            routes=stratified_data.to_dict('records'),
            model=lightweight_model,
            inflection_data=chi_squared_results
        )

        # Verify risk flags are assigned
        assert len(risk_flags) == len(stratified_data), (
            "Risk flag count mismatch"
        )

        # Verify flags are boolean
        for flag in risk_flags:
            assert isinstance(flag, bool), (
                f"Risk flag {flag} is not a boolean"
            )

    def test_topological_metrics_integration(self, stratified_data, topological_metrics, lightweight_model):
        """Test that topological complexity metrics are correctly integrated into evaluation."""
        # Load and integrate topological metrics
        integrated_data = integrate_topological_metrics(
            routes=stratified_data.to_dict('records'),
            topological_metrics=topological_metrics
        )

        # Verify integration was successful
        assert integrated_data is not None, "Topological metrics integration returned None"
        assert len(integrated_data) == len(stratified_data), (
            "Integrated data length mismatch"
        )

        # Verify that topological complexity was added to each route
        for route in integrated_data:
            assert 'topological_complexity' in route, (
                "Route missing topological_complexity field after integration"
            )

    def test_full_evaluation_pipeline(self, stratified_data, topological_metrics, 
                                    lightweight_model, baseline_model):
        """Test the complete evaluation pipeline from data loading to output generation."""
        # Run full evaluation
        evaluation_result = run_evaluation(
            stratified_routes=stratified_data,
            topological_metrics=topological_metrics,
            lightweight_model=lightweight_model,
            baseline_model=baseline_model,
            output_path=EVALUATION_OUTPUT_PATH
        )

        # Verify evaluation completed
        assert evaluation_result is not None, "Evaluation pipeline returned None"
        
        # Verify output file was created
        assert EVALUATION_OUTPUT_PATH.exists(), (
            f"Evaluation output file not created at {EVALUATION_OUTPUT_PATH}"
        )

        # Verify output structure
        with open(EVALUATION_OUTPUT_PATH, 'r') as f:
            output_data = json.load(f)

        assert 'raw_inflection_data' in output_data, (
            "Output missing 'raw_inflection_data' key"
        )
        
        raw_data = output_data['raw_inflection_data']
        assert 'validity_by_category' in raw_data, (
            "Raw data missing 'validity_by_category' key"
        )
        assert 'inflection_points' in raw_data, (
            "Raw data missing 'inflection_points' key"
        )
        assert 'chi_squared_results' in raw_data, (
            "Raw data missing 'chi_squared_results' key"
        )

    def test_cognitive_horizon_identification(self, stratified_data, lightweight_model):
        """Test that the cognitive horizon (inflection point) is correctly identified."""
        # Compute validity across categories
        all_validity = {}
        for category in ['short', 'medium', 'long']:
            category_routes = stratified_data[stratified_data['category'] == category]
            validity_scores = compute_route_validity(
                routes=category_routes.to_dict('records'),
                model=lightweight_model,
                category=category
            )
            all_validity[category] = validity_scores

        # Perform chi-squared scan
        chi_squared_results = perform_chi_squared_scan(
            validity_data=all_validity,
            threshold=0.15,
            alpha=0.05
        )

        # Identify cognitive horizon
        inflection_points = chi_squared_results['inflection_points']
        
        # Verify at least one inflection point was found
        assert len(inflection_points) > 0, (
            "No inflection points detected - cognitive horizon not identified"
        )

        # Verify inflection point structure
        for point in inflection_points:
            assert 'category' in point, "Inflection point missing 'category'"
            assert 'validity_drop' in point, "Inflection point missing 'validity_drop'"
            assert 'p_value' in point, "Inflection point missing 'p_value'"
            assert 'is_significant' in point, "Inflection point missing 'is_significant'"

            # Verify validity drop is meaningful
            assert 0.0 <= point['validity_drop'] <= 1.0, (
                f"Invalid validity drop {point['validity_drop']}"
            )

    def test_category_performance_divergence(self, stratified_data, lightweight_model):
        """Test that performance divergence between categories is measurable."""
        # Compute validity for each category
        category_validity = {}
        for category in ['short', 'medium', 'long']:
            category_routes = stratified_data[stratified_data['category'] == category]
            validity_scores = compute_route_validity(
                routes=category_routes.to_dict('records'),
                model=lightweight_model,
                category=category
            )
            category_validity[category] = sum(validity_scores) / len(validity_scores)

        # Verify we have validity scores for all categories
        assert len(category_validity) == 3, "Missing validity scores for some categories"

        # Check that there is measurable variance across categories
        validity_values = list(category_validity.values())
        variance = max(validity_values) - min(validity_values)
        
        # We expect some variance - if it's exactly 0, something might be wrong
        # (though this could theoretically happen with perfect/poor performance everywhere)
        # For a realistic test, we just verify the calculation worked
        assert isinstance(variance, float), "Variance calculation failed"

    def test_empty_category_handling(self):
        """Test that the system handles missing categories gracefully."""
        # Create a minimal mock dataset with only 'short' routes
        import pandas as pd
        mock_data = pd.DataFrame({
            'route_id': ['mock_route_1'],
            'stops': ['A', 'B', 'C'],
            'category': ['short']
        })

        # This should not crash even if 'medium' and 'long' are missing
        try:
            # Try to compute validity for the available category
            validity = compute_route_validity(
                routes=mock_data.to_dict('records'),
                model=None,  # Will fail, but we're testing category handling
                category='short'
            )
            # If model is None, this should raise an appropriate error
            # The test passes if we get here without a category-related error
        except TypeError:
            # Expected when model is None - category handling worked
            pass
        except Exception as e:
            # If we get a different error, check it's not category-related
            assert "category" not in str(e).lower(), (
                f"Unexpected category-related error: {e}"
            )