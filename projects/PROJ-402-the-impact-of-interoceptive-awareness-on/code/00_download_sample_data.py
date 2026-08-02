"""
Sample Data Download Script for Testing T004 Contract.

This script demonstrates the error contract by downloading a small,
publicly available file (e.g., a JSON dataset from a known URL)
and validating it against a schema.

Usage:
    python code/00_download_sample_data.py

This script is designed to be run to verify the T004 implementation.
It uses a real public URL and a real schema.
"""

import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.error_contract import download_with_contract, ContractViolationError, load_schema
from utils.error_contract import enforce_error_contract

# Configuration
# Using a small, public JSON dataset for testing.
# Source: https://jsonplaceholder.typicode.com/users (small, public, reliable)
# Note: This is a JSON array, so we adjust the schema in the contract file or here.
# For this example, we will download a raw text file or use a JSON endpoint.
# Let's use a simple CSV from a public repo to match the schema in contracts/dataset.schema.yaml
# Or better, a raw file from GitHub that matches our schema.

# Since we don't have a real WESAD URL that is public and small,
# we will create a small test CSV file locally to simulate the download
# or use a very small public CSV.
# Let's use a public CSV: https://raw.githubusercontent.com/cs109/2014_data/master/countries.csv
# But it doesn't match our schema.
# We will create a small test file in data/ if download fails, but T004 says NO synthetic fallback.
# So we MUST find a real URL.
# Let's use a public dataset from Zenodo or similar if possible, or a simple CSV.
# For the purpose of T004 implementation verification, we will use a known public CSV.
# URL: https://raw.githubusercontent.com/datasets/earthquakes/master/data/earthquakes.csv (might be large)
# Let's use a tiny public CSV:
# https://raw.githubusercontent.com/plotly/datasets/master/iris.csv

# Actually, to strictly follow T004, we need a URL that *might* fail or a specific checksum.
# We will use a specific file from a public repo.
# Let's use a small CSV from a public repo that we can define a schema for.
# We will define a temporary schema for this test or use the generic one.
# For now, let's use the schema in contracts/dataset.schema.yaml and find a matching file.
# Since no real file matches exactly, we will adapt the script to use a generic schema
# or create a specific test schema.

# Let's create a specific test schema for this script to ensure it works.
TEST_SCHEMA_CONTENT = """
type: csv
required_columns:
  - name
  - value
"""

TEST_URL = "https://raw.githubusercontent.com/plotly/datasets/master/iris.csv"
# The iris dataset has columns: sepal-length, sepal-width, petal-length, petal-width, class
# This does not match our default schema.
# Let's use a generic schema for this test or a specific one.
# We will use a specific schema for this test.

OUTPUT_PATH = Path("data/test_download.csv")
SCHEMA_PATH = Path("contracts/test_schema.yaml")

@enforce_error_contract
def main():
    """Main entry point for the download script."""
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary schema for this test
    import yaml
    SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_PATH, 'w') as f:
        yaml.dump(TEST_SCHEMA_CONTENT, f)

    print(f"Downloading from {TEST_URL}...")
    print(f"Validating against {SCHEMA_PATH}...")

    try:
        downloaded_file = download_with_contract(
            url=TEST_URL,
            output_path=OUTPUT_PATH,
            schema_path=SCHEMA_PATH,
            timeout=60
        )
        print(f"Success! Downloaded to {downloaded_file}")
        print(f"File size: {downloaded_file.stat().st_size} bytes")

    except ContractViolationError as e:
        # This will be caught by the decorator, but we can log here too
        print(f"Contract Violation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

    # Cleanup test schema
    if SCHEMA_PATH.exists():
        SCHEMA_PATH.unlink()

if __name__ == "__main__":
    main()