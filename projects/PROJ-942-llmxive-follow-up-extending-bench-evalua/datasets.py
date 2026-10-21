"""
Minimal stub of the ``datasets`` library used only for the project's tests.

The real ``datasets`` package pulls in heavy dependencies (e.g., ``pyarrow``)
that are unavailable in the execution environment.  This stub provides a
``load_dataset`` function compatible with the limited usage in the test
suite:

* ``load_dataset("json", data_files=..., recursive=True)`` – loads all
  matching JSON files and returns a simple object with a ``data`` attribute.
* Any other dataset name raises ``NotImplementedError``.
"""

import json
import glob
from types import SimpleNamespace
from pathlib import Path
from typing import Any, List


def load_dataset(name: str, **kwargs: Any) -> SimpleNamespace:
    """
    Very small subset of the ``datasets.load_dataset`` API.

    Parameters
    ----------
    name: str
        The name of the dataset to load. Only ``"json"`` is supported.
    **kwargs:
        Expected keys for the JSON loader:
        - ``data_files``: a glob pattern (string) pointing to JSON files.
        - ``recursive``: bool indicating whether ``**`` patterns should be
          expanded recursively.

    Returns
    -------
    SimpleNamespace
        An object with a single attribute ``data`` containing a list of
        parsed JSON objects.
    """
    if name != "json":
        raise NotImplementedError(
            f"This stub only implements JSON loading; received name={name!r}"
        )

    pattern = kwargs.get("data_files")
    if not pattern:
        raise ValueError("The stub requires a 'data_files' argument for JSON loading.")

    recursive = bool(kwargs.get("recursive", False))

    # Resolve the glob pattern
    matched_files: List[Path] = [
        Path(p) for p in glob.glob(str(pattern), recursive=recursive) if Path(p).is_file()
    ]

    data = []
    for file_path in matched_files:
        with file_path.open("r", encoding="utf-8") as f:
            try:
                data.append(json.load(f))
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON file {file_path}: {e}") from e

    # Return a simple namespace mimicking the real Dataset object
    return SimpleNamespace(data=data)