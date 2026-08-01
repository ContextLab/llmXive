# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was presented showing that the required directories (`data/raw`, `data/processed`, `code`, `tests`, `results`) actually exist under `projects/PROJ-118-investigating-the-neural-correlates-of-p/`. Without a directory listing, screenshots, or any other artifact confirming their creation, the task requirement is not satisfied. The implementer must provide concrete proof that these folders have been created and are non‑empty.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T004` (rejected 1x): I could find no evidence of a `data/raw` or `data/processed` directory, nor any `.gitkeep` files within them. Without these actual artifacts present, the requirement to set up the directory structure is not satisfied. The implementer must add the two directories and place a `.gitkeep` file in each.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: conftest.py
- `T009` (rejected 1x): No code, configuration file, or documentation was presented that defines or manages the `OPENNEURO_API_KEY` environment variable or sets up local path handling. The required artifact (e.g., a `.env` file, a Python module that reads `os.getenv`, or setup instructions) is missing, so the task is not satisfied.
- `T018` (rejected 1x): The provided `code/preprocess.py` is truncated and does not contain any epoching logic or code that writes an `epo_raw.fif` file. Moreover, the required output file `data/processed/epo_raw.fif` is absent from the repository. Both the implementation and the expected artifact are missing.
- `T011` (rejected 1x): The integration test file `tests/integration/test_preprocess.py` exists, but the required output artifact `data/processed/epo_raw.fif` is missing, so the test cannot verify that the pipeline creates a non‑empty epochs file as specified. The missing processed file must be generated (or a mock provided) for the task to be considered complete.
- `T022` (rejected 1x): The required input file `data/processed/epo_raw.fif` does not exist, so `extract.py` cannot load any epochs or compute average ERPs. Additionally, the provided script is truncated and does not show a complete implementation that iterates over participants and outputs the computed ERPs. The core artifact needed to satisfy the task is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

