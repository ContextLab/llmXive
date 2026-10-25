import pytest
from datasets import load_dataset

# Import the constants from the implementation to keep the test aligned with the
# production code.
from code.data.download import REQUIRED_COLUMNS, DATASET_NAME


def test_qm9_columns_present():
    """
    Verify that the QM9 dataset downloaded from HuggingFace contains the required
    columns defined in the specification (SMILES and HOMO).
    """
    ds = load_dataset(DATASET_NAME)
    # Use the first split (e.g., "train") for schema inspection.
    split_name = next(iter(ds))
    dataset = ds[split_name]

    missing = REQUIRED_COLUMNS - set(dataset.column_names)
    assert not missing, f"Missing required columns in QM9 dataset: {missing}"
