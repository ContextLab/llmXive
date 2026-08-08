# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The provided `tests/integration/test_feasibility_gate.py` file is truncated, so we cannot verify that it contains assertions for both the “TCGA < 3” and “GEO < 2” scenarios and that it checks the exact JSON content and halting behavior. Without seeing those assertions, we cannot confirm the test meets the stated requirement. The missing `data/feasibility_gate.json` is expected to be generated at runtime, but the test itself must explicitly validate its contents, which is not demonstrable from the evidence.
- **T012** — declared artifact(s) missing/empty/invalid: src/data_acquisition.py, state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml
- **T013** — declared artifact(s) missing/empty/invalid: src/data_acquisition.py
- **T020** — declared artifact(s) missing/empty/invalid: src/preprocessing.py
- **T023** — declared artifact(s) missing/empty/invalid: src/differential_expression.py
- **T025** — declared artifact(s) missing/empty/invalid: src/meta_analysis.py
