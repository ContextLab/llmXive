# Checksum Manifest Location

The SHA‑256 checksum manifest for all data files is stored directly under the
project's `data/` directory, as required by FR‑007. The following files are
provided:

* `data/checksums.csv` – CSV format listing each data file and its SHA‑256 hash.
* `data/checksums.json` – JSON format version of the same information.
* `data/checksums.sha256` – Plain‑text list of hashes compatible with standard
  verification tools.

These files can be used to verify the integrity of the dataset before any
analysis steps are performed.

