# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The evidence provides only the project root path and contains no configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or scripts) that set up ruff linting or black formatting, nor any documentation or execution logs showing the tools are configured. Without these artifacts, the requirement to configure linting and formatting is not satisfied.
- **T006** — Requested task execution failed; rerun successfully: code/download_data.py exit=1
- **T007** — declared artifact(s) missing/empty/invalid: tests/test_utils.py
- **T008** — the task writes platform-owned path(s) inside the project: `.github/workflows/research.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T009** — The required unit‑test file `tests/test_download_data.py` is missing from the project, so no test for the data‑filtering logic is present. The task cannot be considered fulfilled until this file exists and contains the appropriate tests.
- **T010** — The required artifact `tests/test_preprocess_fmri.py` does not exist in the project repository, so no unit test for the band‑pass filter frequency response is present. The missing file must be added with appropriate test code to satisfy the task.
- **T011** — declared artifact(s) missing/empty/invalid: code/download_data.py, data/processed/behavioral_clean.csv
- **T012** — declared artifact(s) missing/empty/invalid: code/preprocess_fmri.py
- **T013** — declared artifact(s) missing/empty/invalid: code/preprocess_fmri.py
- **T014** — declared artifact(s) missing/empty/invalid: code/preprocess_fmri.py
- **T016** — The required unit‑test file `tests/test_build_graphs.py` is missing from the project, so the adjacency‑matrix thresholding logic is not exercised by any test. The task’s core deliverable does not exist.
- **T017** — The required unit‑test file `tests/test_build_graphs.py` is missing from the project, so the task’s core deliverable does not exist. Without this test the Louvain convergence and seed‑stability verification cannot be satisfied.
- **T021** — Requested task execution failed; rerun successfully: code/build_graphs.py exit=1
