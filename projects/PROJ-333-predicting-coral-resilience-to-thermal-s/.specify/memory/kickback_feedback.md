# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/raw`, `data/processed`, `results/plots`, `specs/001-coral-resilience-prediction/`) being created is present; the implementer only provided a feature specification without any filesystem artifacts. The task’s core requirement—establishing the project directory structure—is therefore unmet.
- `T001b` (rejected 1x): No `.gitignore` file was provided in the evidence, nor any listing of its contents showing the required exclusion patterns (`data/raw/*.fastq.gz`, `data/processed/*.rds`, `__pycache__`, `*.pyc`). The task cannot be considered fulfilled without the actual file.
- `T003a` (rejected 1x): No `.flake8` configuration file is present in the provided evidence, and thus there is no content to verify that it contains `max-line-length = 88` and `ignore = E203,W503`. The required artifact is missing.
- `T003b` (rejected 1x): declared artifact(s) missing/empty/invalid: pypyproject.toml
- `T004b` (rejected 1x): No `specs/001-coral-resilience-prediction/amendments.md` file (or its contents) was presented, so we cannot verify that the change from BioProject PRJNA292777 to PRJNA321023 was documented as required. The required amendment record is missing.
- `T018` (rejected 1x): No files or logs were presented showing a reference transcriptome for *Acropora millepora* placed in `data/raw/reference/`. Without the actual downloaded transcriptome (or verification output), the requirement is not satisfied. The implementer must provide the transcriptome file (or a checksum/log confirming the download) in the specified directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

