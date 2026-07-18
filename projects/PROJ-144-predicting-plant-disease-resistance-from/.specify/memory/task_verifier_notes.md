# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `tests/`, `state/`) was provided; without a directory listing or files, we cannot confirm that the project structure exists. The implementer must create and show these folders (and at least placeholder files) to satisfy the task.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/batch_corrected_matrix.csv, data/processed/labels.csv
- **T019** — The unit‑test file `tests/unit/test_modeling.py` is present and contains a `test_permutation_test` that checks the permutation distribution, but the module it imports (`code/modeling/evaluate.py`) does not exist, so the test cannot be executed. The required implementation file is missing, preventing the task from being truly completed.
- **T021** — declared artifact(s) missing/empty/invalid: code/modeling/evaluate.py
- **T022** — No code, script, notebook, or other artifact implementing VIF calculation and flagging metabolites with VIF > 5 is present; the only information is the task description itself, which does not constitute the required implementation.
- **T023** — No output documentation artifact was provided that demonstrates the findings are framed as “associational.” Without a report, summary, or any written results to inspect, we cannot verify that the implementer has ensured all findings are presented in an associational manner as required by FR‑011. The required artifact is missing.
