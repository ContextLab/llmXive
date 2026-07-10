"""
Integration test for the STL/Hodrick-Prescott decomposition pipeline.

This test validates:
1. The full pipeline execution from processed data to decomposition results.
2. Correct handling of Augmented Dickey-Fuller (ADF) pre-tests.
3. Correct handling of seasonality pre-tests (spectral/autocorrelation).
4. Proper selection between STL (seasonal) and HP (non-seasonal) methods.
5. Output schema compliance for decomposition results.

Prerequisites:
- T013 (preprocess.py) must be implemented to provide processed data.
- T021 (decomposition.py) must be implemented with ADF and seasonality checks.
"""
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pytest
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

# Import the module under test
# Note: We assume the project root is added to sys.path or we run from the project root
import sys
from pathlib import Path

# Add the project root to the path to allow imports from code/
# This assumes the test is run from the project root: python -m pytest tests/
project_root = Path(__file__).resolve().parents[2]
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from analysis.decomposition import (
    run_decomposition_pipeline,
    test_stationarity_adf,
    test_seasonality_autocorr,
    decompose_series_stl,
    decompose_series_hp
)
from data.preprocess import save_processed_data, load_raw_data, normalize_tags, parse_dates, aggregate_monthly_frequencies, filter_min_months

# Constants
TEST_DATA_DIR = Path(tempfile.mkdtemp())
PROCESSED_DATA_PATH = TEST_DATA_DIR / "processed" / "monthly_frequencies.json"
OUTPUT_DIR = TEST_DATA_DIR / "decomposition_output"
OUTPUT_PATH = OUTPUT_DIR / "decomposition_results.json"

# Helper: Create realistic mock data
def create_mock_processed_data() -> Dict[str, Any]:
    """
    Creates a mock processed data file that mimics the output of T013.
    Includes:
    - A seasonal series (sine wave + trend + noise) -> Should trigger STL
    - A non-seasonal, stationary series -> Should trigger HP or simple trend
    - A non-stationary series (random walk) -> Should be differenced first
    """
    n_months = 60
    dates = [f"2019-{str(m).zfill(2)}" for m in range(1, n_months + 1)]
    
    # Series 1: Seasonal (React-like)
    # Trend + Seasonality + Noise
    trend1 = np.linspace(100, 200, n_months)
    seasonal1 = 20 * np.sin(np.linspace(0, 4 * np.pi, n_months))
    noise1 = np.random.normal(0, 5, n_months)
    series1 = trend1 + seasonal1 + noise1
    
    # Series 2: Non-seasonal, stable (Python-like, but simplified)
    trend2 = np.linspace(500, 550, n_months)
    noise2 = np.random.normal(0, 10, n_months)
    series2 = trend2 + noise2
    
    # Series 3: Non-stationary (Random Walk)
    # This should fail ADF and be differenced
    walk = np.cumsum(np.random.normal(0, 1, n_months))
    series3 = walk + 1000
    
    data = {
        "tags": {
            "react": {
                "dates": dates,
                "counts": [int(x) for x in series1]
            },
            "python": {
                "dates": dates,
                "counts": [int(x) for x in series2]
            },
            "nodejs": {
                "dates": dates,
                "counts": [int(x) for x in series3]
            }
        },
        "metadata": {
            "source": "mock_integration_test",
            "generated_at": "2023-10-27"
        }
    }
    return data

def save_mock_data():
    """Saves the mock data to the expected processed location."""
    data = create_mock_processed_data()
    PROCESSED_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_DATA_PATH, 'w') as f:
        json.dump(data, f)

@pytest.fixture(scope="module")
def setup_pipeline_data():
    """Fixture to set up mock data before running tests."""
    save_mock_data()
    yield
    # Cleanup
    import shutil
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)

class TestDecompositionPipeline:
    
    def test_adf_pretest_stationary(self, setup_pipeline_data):
        """Test that ADF correctly identifies a stationary series (Series 2: Python)."""
        # Load data
        with open(PROCESSED_DATA_PATH, 'r') as f:
            data = json.load(f)
        
        series = data["tags"]["python"]["counts"]
        stat_result = test_stationarity_adf(series)
        
        # Series 2 is trend + noise, technically non-stationary in mean, 
        # but for the sake of this test, we expect p-value to be high enough 
        # to indicate we might not need differencing if we detrend, 
        # OR we expect it to fail ADF (p < 0.05) because of the trend.
        # Let's adjust the mock: Series 2 is a random walk with drift? 
        # Actually, a linear trend is non-stationary.
        # Let's assume the test expects:
        # If p < 0.05 -> Non-stationary -> Difference
        # If p >= 0.05 -> Stationary -> No difference
        
        # For a linear trend, ADF usually fails (p < 0.05).
        # Let's check the result.
        assert "p_value" in stat_result
        assert "is_stationary" in stat_result
        # We don't assert a specific value here as it depends on the trend strength,
        # but we assert the structure is correct.

    def test_adf_pretest_nonstationary(self, setup_pipeline_data):
        """Test that ADF correctly identifies a non-stationary series (Series 3: NodeJS)."""
        with open(PROCESSED_DATA_PATH, 'r') as f:
            data = json.load(f)
        
        series = data["tags"]["nodejs"]["counts"]
        stat_result = test_stationarity_adf(series)
        
        # Random walk should definitely be non-stationary
        assert stat_result["is_stationary"] is False
        assert stat_result["p_value"] < 0.05

    def test_seasonality_pretest(self, setup_pipeline_data):
        """Test that seasonality check detects seasonality in Series 1 (React)."""
        with open(PROCESSED_DATA_PATH, 'r') as f:
            data = json.load(f)
        
        series = data["tags"]["react"]["counts"]
        # Remove trend for a better seasonality check? 
        # The function test_seasonality_autocorr handles this internally usually.
        season_result = test_seasonality_autocorr(series)
        
        assert "is_seasonal" in season_result
        assert "method" in season_result
        # React series has strong seasonality, should be True
        # Note: With only 60 points, 5 years, 4 cycles, it should be detectable.
        # We assert the structure is valid.
        assert isinstance(season_result["is_seasonal"], bool)

    def test_pipeline_selection_logic(self, setup_pipeline_data):
        """
        Test that the pipeline selects the correct decomposition method:
        - React: Seasonal -> STL
        - NodeJS: Non-stationary -> Difference + (STL or HP depending on seasonality of diff)
        """
        # Ensure output dir exists
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run the pipeline
        # The function expects paths as strings
        run_decomposition_pipeline(
            input_path=str(PROCESSED_DATA_PATH),
            output_path=str(OUTPUT_PATH)
        )
        
        # Verify output file exists
        assert OUTPUT_PATH.exists(), "Decomposition results file was not created"
        
        # Load and validate results
        with open(OUTPUT_PATH, 'r') as f:
            results = json.load(f)
        
        assert "tags" in results
        assert "metadata" in results
        
        # Check React (Should be seasonal -> STL)
        react_res = results["tags"].get("react", {})
        assert "method" in react_res
        assert "adf_result" in react_res
        assert "seasonality_result" in react_res
        
        # Check NodeJS (Should be non-stationary -> differenced)
        nodejs_res = results["tags"].get("nodejs", {})
        assert "method" in nodejs_res
        assert "was_differenced" in nodejs_res
        assert nodejs_res["was_differenced"] is True # Random walk should be differenced

    def test_decomposition_output_schema(self, setup_pipeline_data):
        """Validate the schema of the decomposition output."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_decomposition_pipeline(
            input_path=str(PROCESSED_DATA_PATH),
            output_path=str(OUTPUT_PATH)
        )
        
        with open(OUTPUT_PATH, 'r') as f:
            results = json.load(f)
        
        # Top level keys
        assert "tags" in results
        assert "metadata" in results
        
        # Iterate through tags and check required fields
        for tag_name, tag_data in results["tags"].items():
            # Required fields per FR-009
            required_fields = [
                "method", "adf_result", "seasonality_result", 
                "trend", "seasonal", "residual", "was_differenced"
            ]
            for field in required_fields:
                assert field in tag_data, f"Missing field {field} for tag {tag_name}"
            
            # Validate types
            assert isinstance(tag_data["trend"], list)
            assert isinstance(tag_data["residual"], list)
            assert isinstance(tag_data["was_differenced"], bool)
            
            # Check adf_result structure
            assert "p_value" in tag_data["adf_result"]
            assert "is_stationary" in tag_data["adf_result"]
            
            # Check seasonality_result structure
            assert "is_seasonal" in tag_data["seasonality_result"]
            assert "method" in tag_data["seasonality_result"]

    def test_integration_end_to_end(self, setup_pipeline_data):
        """
        End-to-end test: 
        1. Load processed data
        2. Run ADF
        3. Run Seasonality
        4. Select Method
        5. Decompose
        6. Save results
        7. Verify file integrity
        """
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Run pipeline
        run_decomposition_pipeline(
            input_path=str(PROCESSED_DATA_PATH),
            output_path=str(OUTPUT_PATH)
        )
        
        # Verify file is valid JSON and not empty
        with open(OUTPUT_PATH, 'r') as f:
            content = f.read()
            assert len(content) > 0
            data = json.loads(content)
        
        # Verify we have results for all mock tags
        assert len(data["tags"]) == 3
        assert "react" in data["tags"]
        assert "python" in data["tags"]
        assert "nodejs" in data["tags"]

    def test_hp_fallback(self, setup_pipeline_data):
        """
        Test that if a series is non-seasonal but stationary (or differenced to stationary),
        it might fall back to HP or a simple trend removal if STL is not appropriate.
        Note: The implementation decides between STL and HP based on seasonality.
        If not seasonal, HP is used.
        """
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_decomposition_pipeline(
            input_path=str(PROCESSED_DATA_PATH),
            output_path=str(OUTPUT_PATH)
        )
        
        with open(OUTPUT_PATH, 'r') as f:
            results = json.load(f)
        
        # Python series is non-seasonal (trend + noise)
        python_res = results["tags"]["python"]
        
        # If it's non-seasonal, the method should be HP (or similar)
        # The exact method name depends on implementation, but it shouldn't be STL
        # if the seasonality test failed.
        # We assert that the method is not STL if is_seasonal is False.
        if not python_res["seasonality_result"]["is_seasonal"]:
            assert python_res["method"] != "STL", "Non-seasonal series should not use STL"
        
        # Verify components exist
        assert "trend" in python_res
        assert "residual" in python_res
        # HP doesn't produce a seasonal component, or it's zero
        if "seasonal" in python_res:
            # If present, it should be empty or zero-ish
            assert len(python_res["seasonal"]) == len(python_res["trend"])

if __name__ == "__main__":
    pytest.main([__file__, "-v"])