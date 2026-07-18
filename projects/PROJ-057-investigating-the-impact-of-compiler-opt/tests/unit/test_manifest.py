import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import the module functions
# The API surface says: from utils.manifest_generator import calculate_sha256, scan_directory, generate_manifest, main
# We assume the test is run from the project root, so we need to add code/ to path or use relative imports if in tests/
# Standard practice for this project structure (tests/ at root, code/ at root):
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.manifest_generator import calculate_sha256, scan_directory, generate_manifest

@pytest.fixture
def temp_project_structure(tmp_path):
    """Create a temporary directory structure mimicking the project."""
    # Create dirs
    data_dir = tmp_path / "data"
    results_dir = data_dir / "results"
    results_dir.mkdir(parents=True)
    
    code_dir = tmp_path / "code"
    kernels_dir = code_dir / "kernels"
    kernels_dir.mkdir(parents=True)
    
    # Create dummy files
    (results_dir / "stability_metrics.csv").write_text("config_id,error\n1,0.001\n")
    (results_dir / "pareto_frontier.png").write_bytes(b"fake_image_data")
    (results_dir / "aggregated.csv").write_text("a,b\n1,2\n")
    (kernels_dir / "matmul.cpp").write_text("// C++ code")
    (data_dir / "manifest.json").write_text("{}") # Should be overwritten or ignored if we scan carefully? No, it will be hashed.
    
    return tmp_path

def test_calculate_sha256(temp_project_structure):
    file_path = temp_project_structure / "data" / "results" / "stability_metrics.csv"
    content = file_path.read_bytes()
    expected_hash = hashlib.sha256(content).hexdigest()
    
    actual_hash = calculate_sha256(file_path)
    assert actual_hash == expected_hash

def test_calculate_sha256_missing_file(temp_project_structure):
    file_path = temp_project_structure / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        calculate_sha256(file_path)

def test_scan_directory(temp_project_structure):
    data_dir = temp_project_structure / "data"
    files = scan_directory(data_dir, extensions=[".csv"])
    # Should find stability_metrics.csv and aggregated.csv
    filenames = [f.name for f in files]
    assert "stability_metrics.csv" in filenames
    assert "aggregated.csv" in filenames
    assert "pareto_frontier.png" not in filenames # Filtered by extension

def test_generate_manifest(temp_project_structure):
    output_path = temp_project_structure / "data" / "manifest.json"
    include_dirs = ["data", "code/kernels"]
    extensions = [".csv", ".png", ".cpp", ".json"]
    
    manifest = generate_manifest(
        base_dir=temp_project_structure,
        output_path=output_path,
        include_dirs=include_dirs,
        extensions=extensions
    )
    
    assert "files" in manifest
    assert len(manifest["files"]) > 0
    
    # Check specific files are present
    keys = list(manifest["files"].keys())
    assert any("stability_metrics.csv" in k for k in keys)
    assert any("pareto_frontier.png" in k for k in keys)
    assert any("matmul.cpp" in k for k in keys)
    
    # Verify hash format
    for path, info in manifest["files"].items():
        assert "sha256" in info
        assert len(info["sha256"]) == 64
        assert "size_bytes" in info

def test_manifest_output_file(temp_project_structure):
    output_path = temp_project_structure / "data" / "new_manifest.json"
    generate_manifest(
        base_dir=temp_project_structure,
        output_path=output_path,
        include_dirs=["data"],
        extensions=[".csv"]
    )
    
    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    assert "files" in data
    assert len(data["files"]) > 0
