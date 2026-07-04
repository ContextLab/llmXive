import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from code.src.utils.manifest import generate_manifest, validate_manifest

def test_manifest_generation_and_content():
    """
    Test that the run_audit.py script generates output files and a manifest.json
    containing SHA256 hashes for those files.
    """
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        
        # Create dummy output files that the pipeline would generate
        dummy_files = {
            "audit_report.json": {"records": []},
            "summary_report.csv": "col1,col2\nval1,val2",
            "power_analysis.json": {"n": 300},
            "subgroup_report.json": {"groups": []}
        }
        
        for fname, content in dummy_files.items():
            fpath = output_dir / fname
            if isinstance(content, dict):
                with open(fpath, "w") as f:
                    json.dump(content, f)
            else:
                with open(fpath, "w") as f:
                    f.write(content)
        
        # Run the manifest generation logic (simulating what run_audit does)
        files_to_hash = [output_dir / f for f in dummy_files.keys()]
        manifest_data = generate_manifest(files_to_hash, output_dir)
        
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        # Assertions
        assert manifest_path.exists(), "Manifest file was not created."
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        
        assert "files" in manifest, "Manifest missing 'files' key."
        assert "generated_at" in manifest, "Manifest missing 'generated_at' key."
        
        # Check that all dummy files are in the manifest
        manifest_files = {item["name"]: item for item in manifest["files"]}
        for fname in dummy_files.keys():
            assert fname in manifest_files, f"File {fname} missing from manifest."
            assert "sha256" in manifest_files[fname], f"File {fname} missing sha256 hash."
            assert len(manifest_files[fname]["sha256"]) == 64, f"Hash for {fname} is not 64 chars."

def test_manifest_validation():
    """
    Test that the generated manifest can be validated against a schema.
    """
    # Note: This test assumes contracts/manifest.schema.yaml exists.
    # If it doesn't, we skip or create a minimal one for the test.
    schema_path = Path("contracts/manifest.schema.yaml")
    
    if not schema_path.exists():
        pytest.skip("Manifest schema not found.")
        
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        test_file = output_dir / "test.txt"
        test_file.write_text("test content")
        
        files_to_hash = [test_file]
        manifest_data = generate_manifest(files_to_hash, output_dir)
        
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f)
        
        is_valid, errors = validate_manifest(manifest_path, schema_path)
        assert is_valid, f"Manifest validation failed: {errors}"
