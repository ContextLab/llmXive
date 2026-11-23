import os
import subprocess
import tempfile
import csv
from pathlib import Path
import pytest

# Assuming the project structure is relative to the test execution
# In a real CI environment, paths would be absolute or relative to repo root
PROJECT_ROOT = Path(__file__).parent.parent.parent
BENCHMARK_DIR = PROJECT_ROOT / "code" / "benchmark"
SCRIPTS_DIR = PROJECT_ROOT / "code" / "scripts"
DATA_DIR = PROJECT_ROOT / "data" / "raw"

@pytest.fixture
def ensure_benchmark_compiled():
    """Ensure the benchmark binary exists before running tests."""
    build_script = SCRIPTS_DIR / "build.sh"
    if not build_script.exists():
        pytest.fail("build.sh not found")
    
    # Run build script
    result = subprocess.run(["bash", str(build_script)], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        pytest.fail("Build failed")
    return BENCHMARK_DIR / "benchmark"

@pytest.fixture
def temp_output_csv():
    """Create a temporary CSV file for testing."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_csv_writer_integration(ensure_benchmark_compiled, temp_output_csv):
    """
    Test that the benchmark binary correctly outputs CSV rows with the required fields:
    thread_count, configuration, iteration_count, wall_clock_time_ms
    """
    binary_path = ensure_benchmark_compiled
    
    # Test parameters
    thread_count = 2
    iterations = 100000
    config = "packed"
    
    # Run the benchmark with specific parameters
    result = subprocess.run(
        [str(binary_path), str(thread_count), str(iterations), config],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Benchmark failed: {result.stderr}"
    
    output_line = result.stdout.strip()
    assert output_line, "Benchmark produced no output"
    
    # Parse the CSV line
    parts = output_line.split(',')
    assert len(parts) == 4, f"Expected 4 CSV fields, got {len(parts)}: {output_line}"
    
    parsed_thread_count = int(parts[0])
    parsed_config = parts[1]
    parsed_iterations = int(parts[2])
    parsed_time = float(parts[3])
    
    assert parsed_thread_count == thread_count
    assert parsed_config == config
    assert parsed_iterations == iterations
    assert parsed_time > 0, "Wall clock time must be positive"
    
    # Verify format matches expected CSV structure
    # The script should append to a file, so let's simulate that
    with open(temp_output_csv, 'w') as f:
        f.write("thread_count,configuration,iteration_count,wall_clock_time_ms\n")
        f.write(output_line + "\n")
    
    # Read back and validate schema
    with open(temp_output_csv, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ["thread_count", "configuration", "iteration_count", "wall_clock_time_ms"]
        
        row = next(reader)
        assert len(row) == 4
        assert row[0] == str(thread_count)
        assert row[1] == config
        assert row[2] == str(iterations)
        assert float(row[3]) > 0

def test_run_benchmarks_script_integration(ensure_benchmark_compiled):
    """
    Test that run_benchmarks.sh executes correctly and generates a CSV file
    with the expected header and data rows.
    """
    run_script = SCRIPTS_DIR / "run_benchmarks.sh"
    output_csv = DATA_DIR / "benchmark_results.csv"
    
    # Ensure output directory exists
    if not output_csv.parent.exists():
        output_csv.parent.mkdir(parents=True)
    
    # Backup existing file if any
    backup = None
    if output_csv.exists():
        backup = output_csv.with_suffix('.csv.bak')
        output_csv.rename(backup)
    
    try:
        # Run the script
        result = subprocess.run(
            ["bash", str(run_script)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"run_benchmarks.sh failed: {result.stderr}"
        
        # Check output file exists
        assert output_csv.exists(), "Output CSV not generated"
        
        # Validate content
        with open(output_csv, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ["thread_count", "configuration", "iteration_count", "wall_clock_time_ms"]
            
            rows = list(reader)
            assert len(rows) > 0, "No data rows generated"
            
            # Check a few rows for valid data
            for row in rows:
                assert len(row) == 4
                assert int(row[0]) > 0
                assert row[1] in ["packed", "padded"]
                assert int(row[2]) > 0
                assert float(row[3]) > 0
    finally:
        # Restore backup if it existed
        if backup and backup.exists():
            output_csv.unlink()
            backup.rename(output_csv)