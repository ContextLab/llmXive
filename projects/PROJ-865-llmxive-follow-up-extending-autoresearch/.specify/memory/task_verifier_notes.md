# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory at the repository root is provided; the claim lacks any artifact verification, so the required directory cannot be confirmed as existing.
- **T001b** — No evidence of a `data/` directory at the repository root is provided; the claim lacks any artifact confirming the directory’s existence. The required folder must be created and shown (e.g., via a directory listing or path confirmation).
- **T001c** — No evidence of a `data/raw/` directory being present in the repository is provided; the artifact list is empty, so the required directory has not been demonstrated as created.
- **T001d** — No evidence of a `data/derived/` directory being present at the repository root was provided; the claim lacks any artifact confirming the directory’s existence.
- **T001e** — No evidence was presented that a `data/artifacts/` directory actually exists in the repository; the response only contains feature specifications and no file‑system listing or screenshots confirming the directory’s creation. The required artifact is missing.
- **T001f** — No evidence of the `specs/001-llmxive-followup/contracts/` directory being present (no directory listing, path confirmation, or files inside) is provided, so the required artifact is missing.
- **T001g** — No artifact showing that the `code/01_data_ingestion/` directory was actually created is provided; the evidence consists only of the task description, with no file‑system listing or screenshot confirming the directory’s existence. The implementer must supply proof (e.g., a directory listing, commit showing the folder, or a screenshot) that the directory now exists and is non‑empty.
- **T001h** — No evidence of the required `code/02_annotation_distillation/` directory being present or populated was provided; the claim lacks any artifact confirming the directory’s creation.
- **T001i** — No evidence was presented showing that a `code/03_execution/` directory actually exists (e.g., a directory listing or confirmation file). Without such proof, we cannot verify the required setup step was performed.
- **T001j** — No evidence was provided that a `code/04_analysis/` directory exists in the repository; the implementer’s claim is unsubstantiated. The required directory must be present (and non‑empty if desired) for the task to be considered complete.
- **T001k** — No evidence of a `code/utils/` directory is provided; the implementer did not supply any artifact confirming its creation, nor any listing or contents of such a folder. Without a visible directory or proof of its existence, the task requirement is not satisfied.
- **T001l** — No evidence was provided showing that a `code/tests/` directory was actually created; the artifact list is empty, so we cannot verify the required directory exists. The implementer must add the directory (and optionally a placeholder file) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or `black` settings) were presented, nor any evidence that ruff and black have been installed or integrated into the project. Without these artifacts, the requirement to configure linting and formatting tools is not satisfied.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — The provided `code/utils/update_state.py` file exists and contains code for hashing and scanning artifacts, but the displayed excerpt ends before any logic that writes or updates `state.yaml` is shown, and the `state.yaml` file itself is missing. Without evidence that the script actually updates the state file, the task’s requirement is not demonstrably fulfilled.
- **T008** — No `.gitignore` file or snippet containing rules for `data/raw/`, `data/derived/`, and `data/artifacts/` was provided; without the actual file content we cannot confirm the required ignore patterns exist. The implementer must supply a `.gitignore` entry (e.g., `data/raw/`, `data/derived/`, `data/artifacts/`) in the repository.
- **T012** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T013b** — The required artifact `data/derived/scope_changes.md` does not exist, so the deviation cannot be documented as specified. The implementer must create this file and record the scope change details.
- **T013d** — No script, configuration, or log evidence is provided showing that `distill_rules.py` was re‑run with a smaller model when T014 coverage fell below 90% and T013b was triggered, nor any re‑validation of coverage. The required retry‑loop implementation and its outcomes are absent.
- **T015** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T016** — No logging code, configuration, or sample log output was provided; there is no artifact demonstrating that annotation counts or rule‑generation metrics are being recorded as required. The implementer’s claim cannot be verified without concrete files or logs.
- **T022** — declared artifact(s) missing/empty/invalid: data/derived/baseline_results.json, data/derived/results.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/derived/results.csv, schema.yaml
- **T026** — declared artifact(s) missing/empty/invalid: data/derived/regression_results.json
- **T027b** — declared artifact(s) missing/empty/invalid: data/derived/results.csv, data/derived/failure_cases.json, data/derived/error_taxonomy_results.json
