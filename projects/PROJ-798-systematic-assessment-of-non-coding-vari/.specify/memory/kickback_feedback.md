# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw/`, `data/derived/`, `tests/`) is provided; the implementer did not supply any artifact showing that the project structure has been created.
- `T004` (rejected 1x): No `.gitignore` file was presented in the evidence, and therefore we cannot confirm that a file exists containing the required exclusion patterns (`data/raw/*` except checksums, `data/derived/*`, `__pycache__`, and `.env`). The implementer must provide the actual `.gitignore` content showing these entries.
- `T008` (rejected 1x): No evidence was presented showing that the `tests/unit/`, `tests/integration/`, and `tests/contract/` directories exist, nor that each contains an `__init__.py` file. The implementer’s claim cannot be verified without these artifacts.
- `T010` (rejected 1x): The provided `code/data_ingestion.py` only defines helper functions (FTP download, logging, checksum, SNP filtering) but the visible portion does not show any execution flow that actually downloads the dbSNP VCF, applies the MAF > 1 % filter, switches to the fallback source when dbSNP is unavailable, or calls `log_source_lineage`. Moreover, the required `data/raw/source_log.txt` file is absent, indicating the logging step has not been performed. The implementation must include the download logic with fallback handling and ensure the source lineage is written to the specified log file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

