import pytest
import pandas as pd
from pathlib import Path
import sys
import os
from pydantic import ValidationError

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the Pydantic schemas defined in the project
from code.analysis.contracts.benchmark_contracts import BenchmarkRun

def test_csv_schema_contract():
    """
    Contract test for CSV output schema.
    Verifies that the benchmark generates a CSV with the required columns
    and that the data validates against the BenchmarkRun Pydantic schema.
    """
    # Expected path based on run_benchmarks.sh
    csv_path = PROJECT_ROOT / "data" / "raw_benchmark_results.csv"
    
    # If the file doesn't exist, we assume the test is run after the benchmark
    if not csv_path.exists():
        pytest.skip(f"CSV file not found at {csv_path}. Run benchmark first.")
    
    df = pd.read_csv(csv_path)
    
    required_columns = [
        "thread_count",
        "configuration",
        "iteration_count",
        "wall_clock_time_ms"
    ]
    
    # Check headers
    missing_cols = [col for col in required_columns if col not in df.columns]
    assert not missing_cols, f"Missing columns in CSV: {missing_cols}"
    
    # Check data types (basic)
    assert df["thread_count"].dtype in ['int64', 'int32', 'float64'], "thread_count should be numeric"
    assert df["configuration"].dtype == 'object', "configuration should be string"
    assert df["iteration_count"].dtype in ['int64', 'int32', 'float64'], "iteration_count should be numeric"
    assert df["wall_clock_time_ms"].dtype in ['int64', 'int32', 'float64'], "wall_clock_time_ms should be numeric"
    
    # Check for non-empty data
    assert len(df) > 0, "CSV must contain at least one data row"
    
    # Check valid configurations
    valid_configs = ["packed", "padded"]
    invalid_configs = df[~df["configuration"].isin(valid_configs)]
    assert len(invalid_configs) == 0, f"Invalid configurations found: {invalid_configs['configuration'].unique()}"
    
    # Check positive values
    assert (df["thread_count"] > 0).all(), "thread_count must be positive"
    assert (df["iteration_count"] > 0).all(), "iteration_count must be positive"
    assert (df["wall_clock_time_ms"] >= 0).all(), "wall_clock_time_ms must be non-negative"
    
    # CONTRACT TEST: Validate each row against the Pydantic BenchmarkRun schema
    # This ensures the data structure strictly matches the defined contract
    failed_validations = []
    for idx, row in df.iterrows():
        try:
            # Map CSV columns to Pydantic model fields
            # Note: BenchmarkRun expects 'configuration' (str), 'thread_count' (int), etc.
            BenchmarkRun(
                thread_count=int(row["thread_count"]),
                configuration=str(row["configuration"]),
                iteration_count=int(row["iteration_count"]),
                wall_clock_time_ms=float(row["wall_clock_time_ms"])
            )
        except ValidationError as e:
            failed_validations.append((idx, str(e)))
    
    assert len(failed_validations) == 0, f"Pydantic validation failed for {len(failed_validations)} rows:\n{failed_validations}"
    
    print("CSV Schema and Contract validation passed.")
