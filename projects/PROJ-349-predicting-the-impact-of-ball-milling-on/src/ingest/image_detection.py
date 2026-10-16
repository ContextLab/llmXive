"""
Image‑detection utility for PSD (Particle Size Distribution) data.

Some ball‑milling experiments report PSD results as images (e.g. scanned
plots) rather than as numeric values. Downstream preprocessing expects
numeric columns ``d10``, ``d50`` and ``d90``. This module provides a simple
detector that scans a ``pandas.DataFrame`` for values that look like image
file references and flags those rows.

The detector is deliberately lightweight – it does **not** attempt to
download or parse the image, only to recognise that the entry is
image‑based so that later stages (e.g. OCR fallback) can handle it.

Usage
-----
>>> import pandas as pd
>>> from src.ingest.image_detection import detect_image_psd
>>> df = pd.DataFrame({
...     "experiment_id": ["exp1", "exp2"],
...     "d10": [10.0, "psd_plot.png"],
...     "d50": [50.0, 55.0],
...     "d90": [90.0, 95.0],
... })
>>> mask = detect_image_psd(df)
>>> mask.tolist()
[False, True]

The function returns a ``pandas.Series`` of booleans indexed like the
original ``DataFrame``; ``True`` indicates that **any** of the PSD columns
contains an image reference.
"""

from __future__ import annotations

import pathlib
import re
from typing import Iterable

import pandas as pd

__all__ = ["detect_image_psd", "is_image_path"]

# Common image extensions – case‑insensitive match.
_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
    ".svg",
}

# Pre‑compiled regex to capture typical URL or file‑path patterns ending
# with a known image extension. This works for plain filenames,
# relative/absolute paths and HTTP/HTTPS URLs.
_IMAGE_REGEX = re.compile(
    r"""(?i)                # case‑insensitive
    (?:https?://)?          # optional scheme
    [\w\-/\.]+              # path characters
    (?:{ext})$              # image extension at end
    """.format(ext="|".join(map(re.escape, _IMAGE_EXTENSIONS))),
    re.VERBOSE,
)

def is_image_path(value: object) -> bool:
    """
    Determine whether ``value`` looks like a reference to an image file.

    Parameters
    ----------
    value : object
        The cell value from a DataFrame. Only ``str`` values are examined;
        all other types are considered non‑image.

    Returns
    -------
    bool
        ``True`` if ``value`` is a string ending with a known image
        extension (case‑insensitive) and matches a simple path/URL pattern.
    """
    if not isinstance(value, (str, pathlib.Path)):
        return False

    # Convert pathlib.Path to string for regex matching.
    val_str = str(value).strip()
    if not val_str:
        return False

    return bool(_IMAGE_REGEX.search(val_str))

def _any_image_in_row(row: pd.Series, columns: Iterable[str]) -> bool:
    """
    Helper: check whether any of the specified ``columns`` in ``row`` contain
    an image reference.
    """
    for col in columns:
        if col in row and is_image_path(row[col]):
            return True
    return False

def detect_image_psd(df: pd.DataFrame) -> pd.Series:
    """
    Scan ``df`` for rows where PSD columns (``d10``, ``d50``, ``d90``) contain
    image references.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame that (at a minimum) contains the columns ``d10``, ``d50``,
        and ``d90``. Additional columns are ignored.

    Returns
    -------
    pandas.Series
        Boolean mask indexed like ``df``; ``True`` indicates that the row
        contains at least one image reference in the PSD columns.

    Notes
    -----
    - The function is tolerant of missing PSD columns – if a column is
      absent it is simply ignored.
    - Empty strings, ``NaN`` values and non‑string types are treated as
      non‑image.
    """
    if df.empty:
        # Return an empty boolean Series with the same index for consistency.
        return pd.Series([], dtype=bool, index=df.index)

    # Determine which PSD columns are present.
    psd_columns = [col for col in ("d10", "d50", "d90") if col in df.columns]

    if not psd_columns:
        # No PSD columns to inspect – return all False.
        return pd.Series([False] * len(df), index=df.index)

    # Apply row‑wise detection.
    mask = df.apply(_any_image_in_row, axis=1, args=(psd_columns,))
    # Ensure the result is a boolean Series (apply may return object dtype).
    return mask.astype(bool)
