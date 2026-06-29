import pandas as pd
from pathlib import Path

def test_ingest_demographics(tmp_path):
    # Create a minimal demographics CSV that matches the expected schema.
    csv_path = tmp_path / "demographics.csv"
    df_input = pd.DataFrame(
        {
            "user_id": [1, 2],
            "age": [34, 45],
            "gender": ["F", "M"],
        }
    )
    df_input.to_csv(csv_path, index=False)

    # Ensure any previous output is removed.
    output_path = Path("data/processed/demographics.csv")
    if output_path.is_file():
        output_path.unlink()

    # Import the function from the project package.
    from adherence_extraction.ingest_demographics import ingest_demographics

    # Run ingestion.
    df_output = ingest_demographics(csv_path)

    # Verify that the output CSV was written and matches the input.
    assert output_path.is_file(), "Output CSV was not created"
    df_written = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(df_written, df_input)
    # Also ensure the function returns the same DataFrame.
    pd.testing.assert_frame_equal(df_output, df_input)
