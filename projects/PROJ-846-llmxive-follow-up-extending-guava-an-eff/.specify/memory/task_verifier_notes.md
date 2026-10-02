# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a Git repository, .gitignore file, or an initial commit is provided; the required artifacts (the .git directory and commit history) are missing.
- **T002a** — The required file `projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/code/requirements.txt` does not exist, even though a similarly named `code/requirements.txt` with the correct contents is present elsewhere. The task specifically demanded the file at the given project path, which is missing.
- **T002b** — The repository lacks a `requirements.txt` file, so the implementer could not run `pip install -r requirements.txt`, and there is no evidence of a virtual environment creation, installation logs, or a `pip freeze` output confirming successful dependency installation. The required artifact and verification steps are missing.
- **T003a** — declared artifact(s) missing/empty/invalid: ruff.toml
- **T005a** — No evidence was provided that a `state/` directory exists in the repository root; the claim is unsubstantiated and the required artifact is missing.
- **T013c** — No code, configuration, or documentation was provided that implements the required graceful‑handling logic for a missing dataset (checking `DATASET_AVAILABLE`, logging, setting the flag, and enabling downstream tasks to skip or use mock data). Without such an artifact, the task’s requirement is not satisfied.
- **T013b** — No artifact (code, script, or generated mock dataset) was provided to demonstrate that a validated synthetic Guava dataset is produced when `DATASET_AVAILABLE` is false in a CI environment. The required fallback generation and its validation are missing.
- **T020** — The required file `data/raw/guava/ground_truth_annotations.json` is missing, so the download and checksum verification steps have not been performed. The task’s core requirement is not satisfied.
- **T021** — No validation script, report, or log for `ground_truth_annotations.json` was provided, nor any evidence (e.g., command output, test results) showing the file was checked against its schema. Consequently the required artifact is missing.
