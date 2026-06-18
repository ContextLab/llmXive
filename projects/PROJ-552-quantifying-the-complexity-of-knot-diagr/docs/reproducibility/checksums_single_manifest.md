# Checksum Manifest

- specs/001-knot-complexity-analysis/contracts/knot_record.schema.yaml Policy

The project maintains a **single authoritative checksum manifest** for each data directory:

* **File:** `checksums.json`
* **Format:** JSON mapping each data file name to its SHA‑256 hash.

Legacy `checksums.csv` and `checksums.sha256` files are deprecated and should be removed to prevent divergence.
