# Version Control and Checksums

This document provides practical guidelines for integrating the project's
checksum manifests with version control (Git). Keeping checksums under version
control ensures that data files can be verified against the exact version used
in any analysis, and it enables automated integrity checks in CI pipelines.

## Why store checksums in VCS?

* **Traceability** – Each commit records the exact checksum values for the data
  files that were present at that point in time.
* **Reproducibility** – Reviewers and collaborators can verify that the data
  they have checked out matches the expected content without needing to run the
  full data‑generation pipeline.
* **Safety** – Accidental corruption or unintended modifications are caught
  early when CI runs the checksum verification step.

## Recommended workflow

1. **Generate checksums** after any data‑processing step using the provided
   `code/reproducibility/run_checksums.py` script. This produces the
   `data/checksums.csv`, `data/checksums.json`, and `data/checksums.sha256`
   manifest files.
2. **Add the manifest files** to the Git index:
   ```bash
   git add data/checksums.csv data/checksums.json data/checksums.sha256
   ```
3. **Commit** with a clear message, e.g., `Add checksum manifests for v1.2
   dataset`.
4. **Push** the commit to the remote repository.

## CI integration

The repository includes a GitHub Actions workflow (`.github/workflows/checksums.yml`)
that automatically runs the checksum verification script on each pull request.
If any checksum mismatches are detected, the workflow fails, preventing the
merge of corrupted or out‑of‑date data.

## Handling large data files

For very large raw data files (e.g., `data/raw/knot_atlas_raw.json`), store only
the checksum in the repository. The raw file itself can be hosted externally
with a URL and a corresponding checksum entry in `data/checksums.csv`. This
approach keeps the repository size manageable while still providing full
verification capabilities.

## Updating checksums

Whenever a data file changes, rerun `run_checksums.py` and commit the updated
manifest files. Do **not** edit checksum files manually; they are generated
programmatically to avoid human error.

---

By following these guidelines, the project maintains a robust link between
version‑controlled source code and the integrity of its data assets.

