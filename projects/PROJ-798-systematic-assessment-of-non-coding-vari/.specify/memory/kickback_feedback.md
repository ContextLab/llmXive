# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory structure (`code/`, `data/raw/`, `data/derived/`, `tests/`) is provided; the implementer did not supply any artifact listing or screenshots showing these folders exist and contain files. The task therefore remains unfinished.
- `T004` (rejected 1x): No `.gitignore` file content or path was provided; without the actual file we cannot verify that it exists, is non‑empty, or contains the required patterns (`data/raw/*` except checksums, `data/derived/*`, `__pycache__`, `.env`). The implementer must supply the `.gitignore` file with the specified exclusions.
- `T008` (rejected 1x): No evidence of the required `tests/unit/`, `tests/integration/`, or `tests/contract/` directories (or their `__init__.py` files) is provided; the implementer did not supply any artifacts showing these folders were created. The task remains undone.
- `T010` (rejected 1x): The provided `code/data_ingestion.py` contains only utilities for downloading JASPAR PWM files and does not implement any logic to fetch common human SNPs from dbSNP (no FTP/`bcftools` handling, no pattern matching for `common_snps.vcf.gz`, no fallback). Additionally, the required `data/raw/source_log.txt` file is absent. These missing components mean the task’s requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

