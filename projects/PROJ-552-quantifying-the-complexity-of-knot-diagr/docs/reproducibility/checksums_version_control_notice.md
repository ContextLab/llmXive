# Version Control & Checksums

This project uses checksum manifests to guarantee the integrity of data files
throughout the development lifecycle.  To ensure reproducibility, **all
checksum files must be tracked in version control** (Git).  The following
guidelines describe how checksums interact with version control:

* **Commit checksum files** (`*.sha256`, `checksums.csv`, `checksums.json`, etc.)
  alongside the data they describe.  This allows reviewers to verify that the
  exact same data were used when the code was executed.
* **Update checksums on data changes** – whenever a data file is added,
  modified, or removed, run the provided checksum generation script
  (`code/reproducibility/run_checksums.py`) and commit the updated checksum
  manifests.
* **Do not ignore checksum files** – ensure that `.gitignore` does **not** contain
  patterns that would exclude these manifests.  The only files that may be
  ignored are large raw data artifacts that are regenerated from authoritative
  sources.
* **Verify integrity in CI** – the continuous‑integration pipeline runs the
  checksum validation step (`code/reproducibility/checksums.py`) to confirm that
  the committed data match their recorded digests.

By keeping checksum files under version control, the repository provides a
transparent, auditable record of data provenance, making it easier for others
to reproduce the analyses exactly as they were performed.

For more detailed instructions, see:

* `docs/reproducibility/checksums.md` – overview of checksum generation.
* `docs/reproducibility/checksums_guidance.md` – best‑practice recommendations.
* `code/reproducibility/run_checksums.py` – command‑line utility to produce and
  validate checksums.

--- End of file ---
