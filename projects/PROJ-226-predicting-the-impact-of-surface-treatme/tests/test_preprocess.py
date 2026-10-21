import pandas as pd
from llmxive_toolkit import paths
import preprocess

def test_preprocess_creates_outputs():
    """
    Run the preprocessing script and verify that the expected output files are created
    and contain no missing values.
    """
    # Execute the preprocessing pipeline
    preprocess.main()

    # Expected output locations
    cleaned_path = paths.data("cleaned", "cleaned.csv")
    impute_path = paths.data("cleaned", "imputation_log.json")
    coverage_path = paths.data("cleaned", "field_coverage.json")

    # Verify that files exist
    assert cleaned_path.is_file(), f"Missing cleaned dataset at {cleaned_path}"
    assert impute_path.is_file(), f"Missing imputation log at {impute_path}"
    assert coverage_path.is_file(), f"Missing field coverage report at {coverage_path}"

    # Load the cleaned dataset and ensure there are no missing values
    df = pd.read_csv(cleaned_path)
    assert not df.isna().any().any(), "Cleaned dataset contains missing values"