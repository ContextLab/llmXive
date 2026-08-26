# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000a` (rejected 1x): No `methodology_rationale.md` file is present in `specs/001-code-complexity-bug-prediction/`, and no content was supplied that documents the conflict between Constitution Principle VI and the required Point‑Biserial/Spearman/Paired Permutation methods. The required artifact is missing.
- `T000b` (rejected 1x): No updated `constitution.md` or `spec.md` file was provided; the evidence shows no artifact at all, so the required amendment document is missing.
- `T001a` (rejected 1x): No evidence of the required folders (`code/`, `code/src/`, `code/tests/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`, `specs/001-exploring-the-relationship-between-code/`) being created is provided; the response only contains specification text and no directory listings or file system artifacts. The task’s core deliverable – the actual project directory structure – is missing.
- `T001c` (rejected 1x): No evidence of a Python 3.11 virtual environment (e.g., a `venv/` directory, activation script, or `pyproject.toml`/`requirements.txt` showing it was created) is present. The implementer provided only a feature specification unrelated to initializing a venv, so the required artifact is missing.
- `T036` (rejected 1x): No `quickstart.md` file or its contents were presented as evidence, so we cannot verify that the required documentation with instructions for `run_pipeline.sh` actually exists. The implementer must add the markdown file and provide its content.
- `T018` (rejected 1x): The claim provides no code, script, or test showing a validation step that checks metric columns for NaN values before writing the CSV. No artifact (e.g., modified extractor script, unit test, or documentation) is present to verify the required behavior. The task therefore remains unfulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

