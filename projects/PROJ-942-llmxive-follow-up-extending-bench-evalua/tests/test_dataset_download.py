import pytest
from datasets import load_dataset, DatasetDict
from llmxive_toolkit import paths

# The official π‑Bench dataset is hosted as "allenai/pi_bench" on the Hub.
DATASET_ID = "allenai/pi_bench"

def test_pi_bench_load():
    """
    Verify that the π‑Bench dataset can be loaded from the raw directory.
    The `datasets` library performs checksum verification during download,
    so a successful load implies that all files match the published SHA‑256
    checksums.
    """
    raw_dir = paths.data("raw")
    ds: DatasetDict = load_dataset(DATASET_ID, data_dir=str(raw_dir))

    # Ensure the dataset object contains at least one split.
    assert ds, "Dataset should contain at least one split."

    # Check that the first split has at least one example.
    first_split = list(ds.keys())[0]
    assert len(ds[first_split]) > 0, f"Split '{first_split}' should contain examples."