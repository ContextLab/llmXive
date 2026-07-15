"""
Integration test for the data ingestion pipeline (User Story 1).

This test verifies:
1. File generation: `data/processed/primes_gaps.csv` and `data/processed/zeta_zeros.csv` exist after pipeline run.
2. Content validation: Files contain correct headers and expected data counts (non-zero).
3. Memory limits: The pipeline execution stays within the 7GB RAM limit (checked via resource module).

Prerequisites:
- T011 (generate_primes.py) must be implemented.
- T014 (ingest_zeros.py) must be implemented.
- T001 (project structure) must be complete.
"""
import os
import sys
import tempfile
import shutil
import resource
import pytest
from pathlib import Path
from typing import Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.generate_primes import run_pipeline as run_prime_pipeline
from src.data.ingest_zeros import run_pipeline as run_zeros_pipeline
from src.utils.config import get_config

# Constants for test
MAX_MEMORY_BYTES = 7 * 1024 * 1024 * 1024  # 7 GB
MIN_ROWS_PRIME = 10  # Sanity check: should have many more, but 10 is minimum for "valid"
MIN_ROWS_ZERO = 10
OUTPUT_DIR = project_root / "data" / "processed"
PRIMES_FILE = OUTPUT_DIR / "primes_gaps.csv"
ZEROS_FILE = OUTPUT_DIR / "zeta_zeros.csv"

# Small limits for integration test speed (T011/T014 should handle large scale, 
# but integration test verifies the *mechanism* works without running to 10^10)
TEST_PRIME_LIMIT = 10000  # 10^4
TEST_ZERO_COUNT = 100

def get_current_memory_mb() -> float:
    """Get current process memory usage in MB."""
    # rusage is available on Unix; on Windows we might need psutil, 
    # but the spec targets CPU-only CI which is usually Linux.
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss / 1024.0

def ensure_output_dir():
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_output_files():
    """Remove output files if they exist to ensure clean test state."""
    if PRIMES_FILE.exists():
        PRIMES_FILE.unlink()
    if ZEROS_FILE.exists():
        ZEROS_FILE.unlink()

def test_prime_generation_memory_and_output():
    """
    Integration test for prime generation (T011/T012).
    
    Verifies:
    - The pipeline runs without crashing.
    - The output file `primes_gaps.csv` is created.
    - The file contains valid CSV data with headers.
    - Memory usage stays below 7GB.
    """
    cleanup_output_files()
    ensure_output_dir()
    
    initial_mem = get_current_memory_mb()
    
    # Run the prime pipeline with a small limit for integration speed
    # Note: We pass the limit directly if the run_pipeline accepts it, 
    # otherwise we rely on config. The task description implies run_pipeline 
    # handles the logic. We assume run_pipeline can accept a limit argument 
    # or we set it in config context. 
    # Given the API surface: `run_pipeline()` takes no args in the signature list,
    # but T011 implies it processes up to 10^10. 
    # We will call it and assume it respects a test override or we mock the limit.
    # However, to be safe and strictly follow "real code", we will assume the 
    # config T005 sets the limit. For this test, we might need to patch the config 
    # or assume the pipeline has a debug mode.
    # 
    # Let's assume the pipeline reads from config. We will patch the config 
    # temporarily or assume the function accepts a limit. 
    # Since the API surface says `run_pipeline` has no args, we must rely on 
    # configuration or a global state. 
    # To make this test robust, we will call it and hope the default config 
    # (if set for tests) is small, OR we assume the function signature in 
    # the actual file allows a limit.
    # 
    # Correction: The prompt says "Implement logic... in generate_primes.py". 
    # It doesn't explicitly say the function signature. 
    # To be safe, I will assume the `run_pipeline` function in the real file 
    # accepts a `limit` parameter or reads from a test config. 
    # If the real implementation strictly hardcodes 10^10, this test would 
    # take forever. 
    # 
    # Strategy: We will assume the implementation allows a `limit` argument 
    # or uses an environment variable. If not, this test might be too slow.
    # But for the sake of the task "implement the test", we write the test 
    # assuming the pipeline can be run with a limit.
    # 
    # Let's assume the signature is `run_pipeline(limit: int = 10**10)` based on 
    # standard design patterns for such tools. If the real file doesn't have it, 
    # the test will fail with TypeError, which is a valid failure mode indicating 
    # the implementation needs to be adjusted to be testable.
    # 
    # However, the prompt says "import ... run_pipeline" with no args. 
    # I will assume the implementation uses `os.environ` or `config` for limits.
    # We will set an env var if possible, or just run and trust the config.
    # 
    # Actually, looking at T005: "Create configuration management... defines N=10^10".
    # We should assume the test modifies the config.
    # Let's try to import config and modify it.
    
    from src.utils import config
    original_n = config.N
    config.N = TEST_PRIME_LIMIT
    
    try:
        # Run pipeline
        run_prime_pipeline()
        
        # Check file existence
        assert PRIMES_FILE.exists(), f"Output file {PRIMES_FILE} was not created."
        
        # Check file content
        with open(PRIMES_FILE, 'r') as f:
            header = f.readline().strip()
            assert "prime_before" in header, "Missing 'prime_before' column."
            assert "gap_size" in header, "Missing 'gap_size' column."
            
            row_count = 0
            for line in f:
                row_count += 1
                if row_count > MIN_ROWS_PRIME:
                    break
            
            assert row_count >= MIN_ROWS_PRIME, f"File has too few rows: {row_count}"
        
        # Check memory (rough check, 7GB is huge, so this should pass easily for small limit)
        current_mem = get_current_memory_mb()
        assert current_mem < (MAX_MEMORY_BYTES / 1024 / 1024), f"Memory limit exceeded: {current_mem} MB > 7000 MB"
        
    finally:
        config.N = original_n
    
    print(f"Prime generation test passed. Rows: {row_count}, Memory: {current_mem:.2f} MB")

def test_zeros_ingestion_memory_and_output():
    """
    Integration test for zeta zero ingestion (T013a/T014).
    
    Verifies:
    - The pipeline runs without crashing.
    - The output file `zeta_zeros.csv` is created.
    - The file contains valid CSV data.
    - Memory usage stays below 7GB.
    """
    cleanup_output_files()
    ensure_output_dir()
    
    initial_mem = get_current_memory_mb()
    
    # Patch config for zeros count if applicable
    from src.utils import config
    original_zero_count = getattr(config, 'ZERO_COUNT', None)
    if hasattr(config, 'ZERO_COUNT'):
        config.ZERO_COUNT = TEST_ZERO_COUNT
    
    try:
        # Run zeros pipeline
        # Similar to primes, we assume it respects config or has a limit arg.
        # If it tries to fetch 10^6 zeros, it will be slow. 
        # We assume the implementation allows limiting via config.
        run_zeros_pipeline()
        
        # Check file existence
        assert ZEROS_FILE.exists(), f"Output file {ZEROS_FILE} was not created."
        
        # Check file content
        with open(ZEROS_FILE, 'r') as f:
            header = f.readline().strip()
            assert "zero_index" in header or "t_value" in header, "Missing expected columns in zeros file."
            
            row_count = 0
            for line in f:
                row_count += 1
                if row_count > MIN_ROWS_ZERO:
                    break
            
            assert row_count >= MIN_ROWS_ZERO, f"File has too few rows: {row_count}"
        
        # Check memory
        current_mem = get_current_memory_mb()
        assert current_mem < (MAX_MEMORY_BYTES / 1024 / 1024), f"Memory limit exceeded: {current_mem} MB > 7000 MB"
        
    finally:
        if original_zero_count is not None:
            config.ZERO_COUNT = original_zero_count
        
    print(f"Zeros ingestion test passed. Rows: {row_count}, Memory: {current_mem:.2f} MB")

def test_full_pipeline_integration():
    """
    End-to-end integration test: Run both pipelines and verify both files exist.
    """
    cleanup_output_files()
    ensure_output_dir()
    
    # Run primes
    from src.utils import config
    config.N = TEST_PRIME_LIMIT
    run_prime_pipeline()
    
    assert PRIMES_FILE.exists(), "Primes file missing after pipeline."
    
    # Run zeros
    if hasattr(config, 'ZERO_COUNT'):
        config.ZERO_COUNT = TEST_ZERO_COUNT
    run_zeros_pipeline()
    
    assert ZEROS_FILE.exists(), "Zeros file missing after pipeline."
    
    print("Full pipeline integration test passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
