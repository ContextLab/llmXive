# Version Control and Checksums

All data artifacts and code in this repository are tracked using Git.
For every released version (tagged commit) a **checksums manifest** is generated
and stored in `data/checksums.sha256`.  The manifest contains SHA‑256 hashes for
all files that are part of the reproducibility bundle (code, data, and
documentation).  This allows downstream users to verify that the files they
download match the exact versions used in the analyses.

The utility `code/reproducibility/run_checksums.py` can be invoked to compare
the current repository state against the recorded manifests:

```bash
python -m code.reproducibility.run_checksums
```
