"""
Unit test for Task T002 implementation.

The test creates a tiny synthetic CSV mimicking the BTS schema,
runs ``code/preprocess.py`` on it, and validates that the output
CSV conforms to ``delay_record.schema.yaml``.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml
import pandas as pd

# Import the helper from llmxive_toolkit for path handling
from llmxive_toolkit import paths

def load_schema():
    schema_path = Path(__file__).parent.parent / "delay_record.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_row(row, schema):
    """Very light validation against the YAML schema."""
    for field in schema["required"]:
        assert field in row, f"Missing required field {field}"
    assert isinstance(row["flight_id"], str)
    assert isinstance(row["total_delay_minutes"], (int, float))
    assert row["total_delay_minutes"] >= 0
    for flag in ["is_anomaly", "is_data_error", "is_zero"]:
        assert isinstance(row[flag], bool)

def test_preprocess_creates_cleaned_csv():
    # Create a minimal CSV with the columns we need
    csv_content = """FlightNum,UniqueCarrier,Origin,Dest,ArrDelay,DepDelay,Cancelled,Diverted
1001,AA,JFK,LAX,10,5,0,0
1002,DL,ORD,SFO,,,-1,0
1003,UA,ATL,MIA,-5,-3,0,0
1004,SW,DEN,PHX,2000,30,0,0
1005,AA,BOS,LHR,15000,0,0,0
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        input_csv = Path(tmpdir) / "sample.csv"
        input_csv.write_text(csv_content)

        # Run the preprocess script
        script_path = Path("code") / "preprocess.py"
        subprocess.run(
            ["python", str(script_path), str(input_csv)],
            check=True,
            cwd=Path.cwd(),
        )

        # Verify output exists
        output_csv = paths.data("processed", "cleaned_delays.csv")
        assert output_csv.is_file(), f"Expected output CSV at {output_csv}"

        df = pd.read_csv(output_csv)

        # Load schema for validation
        schema = load_schema()

        # Validate each row against the schema
        for _, row in df.iterrows():
            validate_row(row.to_dict(), schema)

        # Additional sanity checks
        # Total delay should be non‑negative and computed correctly
        expected_delays = [15, 0, 0, 2030, 15000]  # NaNs treated as 0, negatives dropped
        assert list(df["total_delay_minutes"]) == expected_delays

if __name__ == "__main__":
    test_preprocess_creates_cleaned_csv()