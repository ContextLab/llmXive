import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths

def test_descriptors_novel_exists():
    """The extraction script should produce a non‑empty CSV file."""
    csv_path = paths.data("descriptors_novel.csv")
    # The script may not have been run yet; invoke it directly.
    # Import inside the test to avoid side‑effects during collection.
    from src.pipeline.extract_descriptors_novel import main as extract_main
    extract_main([])

    assert csv_path.is_file(), f"{csv_path} was not created"
    df = pd.read_csv(csv_path)
    # Expect at least one row and the required columns.
    required_cols = {"clip_id", "variance", "autocorr_lag1", "spectral_density"}
    assert not df.empty, "Descriptor CSV is empty"
    assert required_cols.issubset(set(df.columns)), f"Missing columns: {required_cols - set(df.columns)}"
    # No NaN values should be present.
    assert not df.isnull().any().any(), "Descriptor CSV contains null entries"