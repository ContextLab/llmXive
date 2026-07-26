# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): No `ingest.py` script or any code, logs, or output files were presented. Without an actual artifact showing the download logic, rate‑limit backoff, and handling of NIST/Materials Project records, the requirement cannot be confirmed as met. The implementer must supply the `ingest.py` file (non‑empty) that implements the specified functionality.
- `T014` (rejected 1x): No `preprocess.py` script or any code, data files, or logs were presented. Consequently there is no evidence that SMILES strings were converted to molecular graphs with RDKit, nor that records lacking temperature/pH/UV were excluded as required. The task’s deliverable is missing.
- `T016` (rejected 1x): No `preprocess.py` script or any files under `data/raw/` or `data/processed/` with accompanying checksum files were provided. The required implementation that saves raw and processed datasets and generates checksums is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

