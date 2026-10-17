"""
I/O helper utilities for the project.
Provides a ``write_csv_with_flag`` function that writes a pandas DataFrame
to CSV and ensures the first line contains the required
``associational_only=true`` metadata flag.
"""

import csv
from pathlib import Path
from typing import Union

import pandas as pd

def write_csv_with_flag(df: pd.DataFrame, path: Union[str, Path]) -> None:
    """
    Write ``df`` to ``path`` as CSV and prepend a comment line
    ``# associational_only=true`` if it is not already present.

    The function creates parent directories as needed and overwrites any
    existing file.

    Args:
        df: DataFrame to write.
        path: Destination file path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write DataFrame to a temporary CSV string
    csv_string = df.to_csv(index=False)

    # Ensure the flag line is present
    flag_line = "# associational_only=true"
    with path.open("w", newline="", encoding="utf-8") as f:
        f.write(flag_line + "\n")
        f.write(csv_string)
