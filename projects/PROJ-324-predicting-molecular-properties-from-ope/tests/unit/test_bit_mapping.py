import os
import pandas as pd

from analysis.explainability import map_bits_to_substructures

def test_deviation_contexts_file():
    """
    Ensure that the deviation_contexts.csv file is created with the correct
    schema and that no ``matched_substructure`` entries are empty.
    """
    # Remove any existing file to guarantee fresh generation
    output_path = 'data/derived/deviation_contexts.csv'
    if os.path.exists(output_path):
        os.remove(output_path)

    # Run the mapping with a modest K to keep runtime reasonable
    map_bits_to_substructures(k=30)

    # Load the generated CSV
    df = pd.read_csv(output_path)

    # Expected columns (order matters for the contract)
    expected_columns = ['smiles', 'bit_index', 'matched_substructure', 'interaction_strength']
    assert list(df.columns) == expected_columns, "CSV header does not match the contract."

    # No empty cells in the matched_substructure column
    assert not df['matched_substructure'].isnull().any(), "Found null values in matched_substructure."
    assert (df['matched_substructure'] != '').all(), "Found empty strings in matched_substructure."