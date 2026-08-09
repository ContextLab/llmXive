# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was presented that the required directories (`code/`, `data/`, `tests/`, `artifacts/`) actually exist in the project repository; the response contains only the task description without any file‑system listing or screenshots. The implementer must provide a directory tree or similar proof that the specified structure has been created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present in the provided evidence, so the claim that linting/formatting tools have been configured cannot be verified. The required artifacts are missing.
- `T009` (rejected 1x): No CI configuration file (e.g., a GitHub Actions workflow YAML) or any other artifact specifying a CPU‑only environment with a 7 GB RAM limit was presented. Without such a file, the claim of having set up the CI environment cannot be verified. The required artifact is missing.
- `T010` (rejected 1x): The claim provides only the task description; there is no actual artifact such as a processed set of 50 manually annotated stories, the resulting “first‑person density” scores, or a reported correlation ≥ 0.8 with human annotations. Without these concrete data files or results, the requirement is not satisfied.
- `T017` (rejected 1x): No code, script, or data artifact was provided that adds the required validation logic to flag “neutral/omniscient” texts when `pronoun_density_1st` is 0.0. The implementer’s claim is unsupported; the repository contains no new files, functions, or test results demonstrating the requested feature. The missing artifact is the implementation (e.g., updated extraction script) and evidence (e.g., JSON output, unit test) showing the flagging behavior.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

