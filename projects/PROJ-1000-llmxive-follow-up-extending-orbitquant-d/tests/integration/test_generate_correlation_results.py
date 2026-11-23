import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from analysis.generate_correlation_results import load_raw_data_points, main

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    data_dir = Path(temp_dir)
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir
    shutil.rmtree(temp_dir)

def test_load_raw_data_points_integration(temp_data_dir):
    """
    Integration test for load_raw_data_points.
    Creates mock CSV files and verifies the merging logic.
    """
    # Setup mock config
    class MockConfig:
        data_dir = temp_data_dir

    # Create mock entropy file
    entropy_file = temp_data_dir / "processed" / "entropy_scores.csv"
    with open(entropy_file, 'w', newline='') as f:
        f.write("prompt_id,entropy_score\n")
        f.write("id_001,1.23\n")
        f.write("id_002,2.45\n")
        f.write("id_003,0.98\n")

    # Create mock variance file
    variance_file = temp_data_dir / "processed" / "activation_variances.csv"
    with open(variance_file, 'w', newline='') as f:
        f.write("prompt_id,variance_value\n")
        f.write("id_001,0.55\n")
        f.write("id_002,0.72\n")
        f.write("id_004,0.11\n") # This one should be dropped (no entropy)

    # Run function
    data = load_raw_data_points(MockConfig())

    assert len(data) == 2, "Should only merge common IDs (id_001, id_002)"
    
    # Verify content
    ids = {d['prompt_id'] for d in data}
    assert ids == {'id_001', 'id_002'}
    
    # Verify values
    d0 = next(d for d in data if d['prompt_id'] == 'id_001')
    assert abs(d0['entropy'] - 1.23) < 1e-5
    assert abs(d0['variance'] - 0.55) < 1e-5

def test_main_generates_json(temp_data_dir, caplog):
    """
    Integration test for main().
    Ensures the script generates the expected JSON file with correct structure.
    """
    # Setup mock config
    class MockConfig:
        data_dir = temp_data_dir

    # Create mock data
    entropy_file = temp_data_dir / "processed" / "entropy_scores.csv"
    with open(entropy_file, 'w', newline='') as f:
        f.write("prompt_id,entropy_score\n")
        f.write("id_001,1.0\n")
        f.write("id_002,2.0\n")
        f.write("id_003,3.0\n")

    variance_file = temp_data_dir / "processed" / "activation_variances.csv"
    with open(variance_file, 'w', newline='') as f:
        f.write("prompt_id,variance_value\n")
        f.write("id_001,10.0\n")
        f.write("id_002,20.0\n")
        f.write("id_003,30.0\n")

    # Mock Config in the module scope if needed, but here we rely on the function
    # We need to patch the Config import in generate_correlation_results
    # For this test, we will directly call the logic that main() does, 
    # or we can temporarily replace Config.
    
    # Let's just verify the file creation by temporarily patching Config
    import analysis.generate_correlation_results as mod
    original_config = mod.Config
    mod.Config = MockConfig

    try:
        output_path = temp_data_dir / "processed" / "correlation_results.json"
        main()
        
        assert output_path.exists(), "Output JSON file was not created"
        
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        assert "metadata" in results
        assert "statistics" in results
        assert "raw_data_points" in results
        
        stats = results["statistics"]
        assert "pearson_r" in stats
        assert "p_value" in stats
        assert "is_significant" in stats
        
        # With perfect linear correlation (1, 10), (2, 20), (3, 30), r should be 1.0
        assert abs(stats["pearson_r"] - 1.0) < 1e-6
        assert stats["p_value"] < 0.05
        assert stats["is_significant"] is True
        
        assert len(results["raw_data_points"]) == 3
    finally:
        mod.Config = original_config
