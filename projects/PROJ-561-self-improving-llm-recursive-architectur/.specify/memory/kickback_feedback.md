# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file contents were provided, so there is no evidence that the required folders (`code/`, `data/raw/`, `data/processed/`, `results/`, `specs/`, `tests/`, `tests/unit/`, `tests/integration/`) exist, nor that `__init__.py` files were created inside them. The implementer must supply the actual project tree or screenshots showing these directories and init files.
- `T004` (rejected 1x): No `utils/memory.py` file or its contents are present in the provided evidence, and thus the required function with gradient checkpointing, batch‑size auto‑scaling, and RAM watchdog is missing. The task is not satisfied.
- `T005a` (rejected 1x): No `pipeline/loader.py` file or its contents were provided, so we cannot verify that loaders for OpenWebText, GSM8K, ARC‑Challenge, and Wikitext‑2 have been implemented with fail‑fast logic and without synthetic fallbacks. The required code artifact is missing.
- `T005b` (rejected 1x): No code for `pipeline/loader.py` was provided, and there is no evidence that an exponential backoff wrapper with the specified initial delay of 30 seconds and a maximum of 5 retries for HuggingFace API calls has been added. The required implementation is missing.
- `T006` (rejected 1x): No `pipeline/model.py` file or any code implementing GPT loading with a medium‑sized configuration and CPU‑compatible weight manipulation is present. The required artifact is missing, so the task is not satisfied.
- `T013` (rejected 1x): No `schemas/modification_proposal.py` file or Pydantic model `ModificationProposal` with the required fields was presented; the evidence does not show the artifact exists or contains the specified schema. The implementer must add the file with the proper model definition.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

