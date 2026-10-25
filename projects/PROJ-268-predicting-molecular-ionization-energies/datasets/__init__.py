"""
Minimal stub of the ``datasets`` library used only for schema verification in tests.
It provides a ``load_dataset`` function that returns a mapping of split names to
simple objects exposing a ``column_names`` attribute.  The implementation fetches
the dataset's ``dataset_infos.json`` from HuggingFace and extracts the feature
names, avoiding heavy dependencies such as ``pyarrow``.
"""
import json
from pathlib import Path
from typing import Dict

from huggingface_hub import hf_hub_download

class SimpleDataset:
    """A tiny container exposing only the attributes required by the test suite."""
    def __init__(self, column_names):
        self.column_names = column_names

def load_dataset(repo_id: str) -> Dict[str, SimpleDataset]:
    """
    Load a minimal representation of a HuggingFace dataset.

    Parameters
    ----------
    repo_id: str
        The repository identifier, e.g. ``'deepchem/qm9'``.

    Returns
    -------
    dict
        Mapping from split name (e.g., ``'train'``) to ``SimpleDataset`` instances.
    """
    # Retrieve the dataset metadata that lists feature names.
    info_path = hf_hub_download(repo_id=repo_id, filename="dataset_infos.json")
    with Path(info_path).open("r", encoding="utf-8") as f:
        info = json.load(f)

    features = info.get("features", {})
    column_names = list(features.keys())

    # Return a single split named ``train`` – the test only inspects the first split.
    return {"train": SimpleDataset(column_names)}
