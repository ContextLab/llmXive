# Documentation: `download_and_checksum`

The function `download_and_checksum` is defined in `code/pipeline/loader.py` and provides the following capabilities required by task **T001b**:

- **Download a HuggingFace dataset** (e.g., `"ag_news"` used in the unit test) into a specified destination directory.
- **Save the dataset to disk** using the `save_to_disk` method, ensuring reproducibility.
- **Compute a SHA‑256 checksum** of the entire directory (excluding any existing checksum files) via `calculate_directory_checksum`.
- **Write the checksum** to a `SHA256SUM` file placed alongside the downloaded data.
- **Idempotency**: if a `SHA256SUM` file already exists, the function reads and returns the cached checksum without re‑downloading the dataset.

## Usage

```python
from pipeline.loader import download_and_checksum

dataset_name = "ag_news"
dest_dir = "data/raw/ag_news"

checksum = download_and_checksum(dataset_name, dest_dir)
print(f"Dataset checksum: {checksum}")
```

This behavior satisfies the unit tests in `tests/unit/test_data_loader.py`:

1. **`test_download_and_checksum_writes_sha256`** verifies that a real HuggingFace dataset is downloaded [UNRESOLVED-CLAIM: c_bbfe9f15 — status=not_enough_info], a 64‑character SHA‑256 hex digest is returned [UNRESOLVED-CLAIM: c_7a710370 — status=not_enough_info], the `SHA256SUM` file is created, and its contents match an independently computed directory checksum [UNRESOLVED-CLAIM: c_e8842a1e — status=not_enough_info].
2. **`test_download_and_checksum_is_idempotent`** confirms that a second call re‑uses the existing checksum file without re‑downloading the data [UNRESOLVED-CLAIM: c_4d9ea99d — status=not_enough_info].

The implementation relies on the `datasets` library (declared in `code/requirements.txt`) and standard Python modules (`os`, `hashlib`, `logging`). It adheres to the project's **FR‑011** exponential back‑off policy via the `@exponential_backoff` decorator defined in the same module.