"""
Integration tests for the benchmark generator script.
"""
import os
import sys
import tempfile
import shutil
import subprocess

def test_benchmark_script_runs():
    """
    Test that the benchmark script runs without crashing on a small sample.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "benchmark_output")
        cmd = [
            sys.executable,
            "code/data/benchmark_generator.py",
            "--num-samples", "10",
            "--target-count", "20",
            "--output-dir", output_dir,
            "--seed", "42"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        assert result.returncode == 0, f"Script failed with stdout: {result.stdout}, stderr: {result.stderr}"
        assert "Benchmark Results" in result.stdout
        assert "STATUS: PASS" in result.stdout or "STATUS: FAIL" in result.stdout
        
        # Verify output directory was created
        assert os.path.exists(output_dir)

def test_benchmark_script_output_structure():
    """
    Test that the benchmark script produces the expected output structure
    by running a small benchmark and checking for generated files.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = os.path.join(tmpdir, "benchmark_output")
        cmd = [
            sys.executable,
            "code/data/benchmark_generator.py",
            "--num-samples", "5",
            "--target-count", "10",
            "--output-dir", output_dir,
            "--seed", "42"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        
        # Check for at least one image and one metadata file
        files = os.listdir(output_dir)
        assert len(files) > 0, "No files generated in output directory"
        
        # Expecting .png or .jpg and .json
        has_image = any(f.endswith('.png') or f.endswith('.jpg') for f in files)
        has_json = any(f.endswith('.json') for f in files)
        
        assert has_image, "No image files generated"
        assert has_json, "No metadata JSON files generated"
