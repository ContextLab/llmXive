"""
Minimal stub for the `datasets` library to avoid heavy dependencies like `pyarrow`
during testing. Provides only the `load_dataset` function used in this project.
"""
from typing import Any, Dict, Iterable, List

class _DummyDataset:
    """A simple iterable placeholder returned by `load_dataset` for JSON files."""

    def __init__(self, data_files: str):
        self.data_files = data_files

    def __iter__(self) -> Iterable[Dict[str, Any]]:
        # No actual data is needed for the tests; they only check that loading succeeds.
        return iter([])

    def __len__(self) -> int:
        return 0

def load_dataset(name: str, *args, **kwargs) -> Any:
    """
    Minimal implementation supporting only the `"json"` format required by the
    test suite. For any other dataset name, an informative ImportError is raised.

    Parameters
    ----------
    name: str
        Dataset identifier (e.g., `"json"` or `"pi_bench"`).

    Returns
    -------
    Any
        Either a dummy dataset object (for `"json"`), or raises ImportError.
    """
    if name == "json":
        data_files = kwargs.get("data_files", "")
        return _DummyDataset(data_files)
    # For all other names we deliberately raise ImportError – the project
    # code falls back to a real download (or, for pi_bench, uses a custom HTTP fetch).
    raise ImportError(
        f"The stubbed `datasets` library only supports the 'json' format. "
        f"Requested dataset: {name}"
    )
