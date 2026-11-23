# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: src/data/loaders.py
- **T009** — The implementer provided no configuration files, scripts, or documentation for environment management or checksum verification of raw downloads; no artifacts exist to demonstrate that these requirements were addressed. The task remains unfulfilled.
- **T012** — The required file `src/data/fetch_gbif.py` does not exist, so no code was provided to retrieve GBIF records, deduplicate them, or perform spatial thinning. The task’s core artifact is missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/data/fetch_climate.py
- **T015** — declared artifact(s) missing/empty/invalid: src/modeling/metrics.py
- **T016** — No code, tests, or documentation showing that error handling for “No occurrence records” and “Model training failure” (with retry using a reduced `max_depth`) was added. The required artifact (e.g., updated pipeline scripts, exception handling logic, and corresponding unit/integration tests) is missing, so the task is not satisfied.
- **T017** — The implementer provided no code, configuration, or log files that add provenance or thinning‑statistics logging, nor any evidence (e.g., screenshots, test outputs) showing such logging in action. Consequently the required artifact is missing.
- **T025** — No code, configuration, or documentation was provided that shows an added disclaimer in the report generation step, nor any evidence (e.g., diff, test, or generated report) demonstrating that relationships are now framed as associative rather than causal. The required artifact is missing.
- **T025b** — No documentation file or excerpt was provided that explains the Trait Imputation strategy as a Plan override of Spec FR‑004. The required explicit description in the final report is missing, so the task is not satisfied.
- **T025c** — No research.md or plan.md file containing a formal note about the Spec‑Plan divergence for Trait Imputation (FR‑004 override) was provided; the required documentation artifact is missing.
- **T027** — The required artifact `tests/integration/test_sensitivity.py` does not exist in the repository, so the integration test for the sensitivity analysis sweep is missing. The task cannot be considered complete until this file is added with appropriate test code.
