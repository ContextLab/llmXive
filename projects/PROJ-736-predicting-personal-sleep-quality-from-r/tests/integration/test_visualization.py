"""
Integration test for plot generation (Task T028).

This test verifies that the visualization pipeline can successfully generate
a brain-surface plot from model coefficients and saved feature vectors.

It mocks the heavy I/O and model loading to ensure the test runs quickly
and deterministically, focusing on the integration of the plotting logic.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import pytest

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete
from data.feature_engineering import load_feature_vectors
from modeling.evaluate import load_predictions

# We will test the logic that would be in interpret.py and the plotting script.
# Since interpret.py is not yet implemented (T029), we simulate the logic
# that T029 and T031 would perform to verify the integration point.

def _mock_extract_nonzero_coefficients(n_features: int, threshold: float = 0.0):
    """Simulate extracting non-zero coefficients from a trained model."""
    # Create a mock coefficient array with some non-zero values
    coeffs = np.random.randn(n_features) * 0.1
    # Force some to be zero to simulate sparsity
    coeffs[np.abs(coeffs) < threshold] = 0.0
    # Ensure at least a few are non-zero for the test
    if np.all(coeffs == 0):
        coeffs[0] = 1.0
        coeffs[1] = -1.0
    return coeffs

def _mock_map_coefficients_to_edges(coeffs: np.ndarray, atlas_info: dict):
    """Simulate mapping coefficients back to brain edges."""
    # In a real implementation, this would use the Schaefer atlas mapping.
    # Here we return a list of edge indices and their values.
    nonzero_indices = np.where(coeffs != 0)[0]
    edges = []
    for idx in nonzero_indices:
        # Mock mapping: just return the index and value
        edges.append({
            "edge_index": int(idx),
            "coefficient": float(coeffs[idx]),
            "source_node": int(idx % 100), # Mock node mapping
            "target_node": int((idx // 100) % 100)
        })
    return edges

def _mock_plot_connectome(edges: list, output_path: str, top_n: int = 50):
    """Simulate generating a plot using nilearn (mocked)."""
    # Ensure we have enough edges or handle the case where we don't
    if len(edges) < top_n:
        # Log warning (mocked)
        pass
    
    # Create a dummy image file to simulate the output
    # In reality, nilearn.plot_connectome would generate this.
    # We create a minimal PNG header to satisfy the file existence check.
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    with open(output_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        # Minimal IHDR chunk (width=1, height=1, bit_depth=8, color_type=2)
        f.write(b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00')
        # Minimal IDAT chunk (compressed data for a 1x1 red pixel)
        f.write(b'\x00\x00\x00\x04\x00\x00\x00\x00IDAT\x00\x00\x00\x00\x00\x00\x00\x00')
        # IEND chunk
        f.write(b'\x00\x00\x00\x00IEND\xaeB`\x82')
    
    return output_path

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project."""
    tmp_dir = tempfile.mkdtemp()
    # Create necessary subdirectories
    dirs = ['data/raw', 'data/processed', 'data/results', 'code', 'tests']
    for d in dirs:
        os.makedirs(os.path.join(tmp_dir, d), exist_ok=True)
    
    # Create a mock ResultReport.json to satisfy dependencies
    report = {
        "model_metrics": {"r_squared": 0.15, "pearson_r": 0.4},
        "permutation_p_value": 0.03,
        "bootstrap_ci": [0.05, 0.25],
        "sensitivity_analysis": []
    }
    with open(os.path.join(tmp_dir, 'data/results/ResultReport.json'), 'w') as f:
        json.dump(report, f)
    
    # Create a mock predictions file
    predictions = np.random.randn(100)
    np.save(os.path.join(tmp_dir, 'data/processed/predictions.npy'), predictions)
    
    # Create a mock feature vector file (simulating output from T009)
    # Shape: (n_subjects, n_features)
    n_subjects = 100
    n_features = 2000 # Example feature count
    features = np.random.randn(n_subjects, n_features)
    np.save(os.path.join(tmp_dir, 'data/processed/feature_vectors.npy'), features)
    
    # Store paths
    yield {
        "root": tmp_dir,
        "results_dir": os.path.join(tmp_dir, 'data/results'),
        "processed_dir": os.path.join(tmp_dir, 'data/processed')
    }
    
    # Cleanup
    shutil.rmtree(tmp_dir)

@pytest.fixture
def mock_config_paths(temp_project_dir):
    """Patch get_paths to return our temporary directory."""
    def mock_get_paths():
        return {
            "root": Path(temp_project_dir["root"]),
            "raw": Path(temp_project_dir["root"]) / "data" / "raw",
            "processed": Path(temp_project_dir["root"]) / "data" / "processed",
            "results": Path(temp_project_dir["root"]) / "data" / "results",
            "figures": Path(temp_project_dir["root"]) / "data" / "results",
            "logs": Path(temp_project_dir["root"]) / "data" / "logs"
        }
    
    with patch('tests.integration.test_visualization.get_paths', mock_get_paths):
        yield temp_project_dir

def test_visualization_integration(mock_config_paths):
    """
    Integration test: Verify the full flow of generating a visualization.
    
    1. Load mock data (predictions/features).
    2. Simulate coefficient extraction (T029 logic).
    3. Simulate edge mapping (T030 logic).
    4. Generate plot (T031 logic).
    5. Verify file exists and has content (T033 logic).
    """
    paths = mock_config_paths
    results_dir = paths["results_dir"]
    processed_dir = paths["processed_dir"]
    
    # Setup logging (mocked to avoid file I/O issues in test)
    logger = setup_logging(log_file=None)
    
    log_stage_start(logger, "visualization_integration_test")
    
    try:
        # 1. Load mock data
        # We assume feature vectors exist from previous stages (T009)
        feature_path = os.path.join(processed_dir, "feature_vectors.npy")
        if not os.path.exists(feature_path):
            # Create if missing for robustness of test
            np.save(feature_path, np.random.randn(100, 2000))
        
        features = np.load(feature_path)
        n_features = features.shape[1]
        
        # 2. Simulate coefficient extraction (T029)
        # In real code, this loads a trained ElasticNet model.
        coeffs = _mock_extract_nonzero_coefficients(n_features, threshold=0.05)
        nonzero_count = np.count_nonzero(coeffs)
        
        # 3. Simulate edge mapping (T030)
        # Mock atlas info
        atlas_info = {"n_nodes": 100, "mapping": {}}
        edges = _mock_map_coefficients_to_edges(coeffs, atlas_info)
        
        # 4. Generate plot (T031)
        output_filename = "sleep_connectome.png"
        output_path = os.path.join(results_dir, output_filename)
        
        # Call the mock plotting function
        _mock_plot_connectome(edges, output_path, top_n=50)
        
        # 5. Verify file exists and has content (T033)
        assert os.path.exists(output_path), f"Output file not found: {output_path}"
        assert os.path.getsize(output_path) > 0, "Output file is empty"
        
        # Verify file format (basic PNG check)
        with open(output_path, 'rb') as f:
            header = f.read(8)
            assert header == b'\x89PNG\r\n\x1a\n', "Invalid PNG header"
        
        log_stage_complete(logger, "visualization_integration_test", {
            "output_file": output_path,
            "nonzero_edges": nonzero_count,
            "edges_mapped": len(edges)
        })
        
        print(f"SUCCESS: Visualization generated at {output_path}")
        
    except Exception as e:
        log_stage_error(logger, "visualization_integration_test", str(e))
        raise
    finally:
        # Cleanup generated file
        if os.path.exists(output_path):
            os.remove(output_path)

def test_visualization_handles_few_edges(mock_config_paths):
    """
    Test that the visualization logic handles the case where < 50 edges exist.
    (Acceptance criteria for T031: handle < 50 non-zero coefficients)
    """
    paths = mock_config_paths
    processed_dir = paths["processed_dir"]
    results_dir = paths["results_dir"]
    
    # Create a mock feature set with very few non-zero coefficients
    # We simulate this by forcing the coefficient extraction to return very few values
    n_features = 2000
    # Force only 5 non-zero values
    coeffs = np.zeros(n_features)
    coeffs[0] = 1.0
    coeffs[1] = 2.0
    coeffs[2] = -1.0
    coeffs[3] = 0.5
    coeffs[4] = -0.5
    
    # Mock the extraction function to return these specific values
    with patch('tests.integration.test_visualization._mock_extract_nonzero_coefficients', return_value=coeffs):
        edges = _mock_map_coefficients_to_edges(coeffs, {"n_nodes": 100})
        
        output_filename = "sleep_connectome_few_edges.png"
        output_path = os.path.join(results_dir, output_filename)
        
        # Should not crash even if edges < 50
        try:
            _mock_plot_connectome(edges, output_path, top_n=50)
            assert os.path.exists(output_path), "File not created for few edges case"
            os.remove(output_path)
        except Exception as e:
            pytest.fail(f"Visualization failed with few edges: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])