"""
Writes the (placeholder) statistical results to CSV.
"""

import pandas as pd

def write_connectivity_results(df, output_path: str):
    """
    Write the connectivity statistics DataFrame to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Statistical results (may be empty).
    output_path : str
        Destination file path.
    """
    pd.DataFrame(df).to_csv(output_path, index=False)
