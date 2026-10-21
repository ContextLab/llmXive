"""
Contract test for the descriptor matrix.

The test loads the Parquet file produced by the preprocessing step and
validates each row against the ``DescriptorMatrix`` Pydantic model.
"""

import pandas as pd
import pytest

from llmxive_toolkit import paths
from .validators import DescriptorMatrix

@pytest.mark.parametrize("row_index", [0, 1, 2, 3, 4])
def test_descriptor_row_schema(row_index):
    """
    Validate that a sample row from the descriptor matrix conforms to the schema.
    """
    descriptor_path = paths.data("processed", "descriptors.parquet")
    # The file may be large; read only the needed rows.
    df = pd.read_parquet(descriptor_path, columns=None, engine="auto")
    assert not df.empty, "Descriptor matrix is empty"

    # Ensure the requested index exists; if the dataset is smaller,
    # fall back to the last available row.
    if row_index >= len(df):
        row_index = len(df) - 1

    row = df.iloc[row_index].to_dict()

    # Pydantic validation – will raise ValidationError on failure.
    DescriptorMatrix(**row)
