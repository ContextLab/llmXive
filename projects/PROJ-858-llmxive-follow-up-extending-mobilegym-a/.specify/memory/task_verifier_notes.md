# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — declared artifact(s) missing/empty/invalid: data/raw/.checksums.txt
- **T011** — declared artifact(s) missing/empty/invalid: data/processed/scheduler_trace.json
- **T012** — The `code/utils/constants.py` file contains no definitions for semantic state proxies nor any logic to read `contracts/coverage.schema.yaml`. Additionally, the required `contracts/coverage.schema.yaml` (or `schema.yaml`) file is missing entirely, so the list of proxies cannot be sourced. Both the constant definitions and the source schema are absent.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/scheduler_trace.json
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/coverage_vectors.json
- **T029** — The implementer did not provide any artifact (e.g., a dataset file, script output, or documentation) showing a held‑out test set that excludes state variables present in the training‑time State Coverage Vector. No evidence of generation, contents, or verification of such a set is present, so the task requirement is unmet.
- **T036** — No plot files or any other artifacts were provided in `data/processed/` (or elsewhere) showing a “Success Rate vs. Steps” visualization. The required output—a saved plot image or data file—simply does not exist, so the task is not satisfied.
- **T040** — The submission contains no code, configuration, tests, or documentation that implements the required logic to flag “Invalid Proxy” when r < 0.3 nor any recommendation to expand the variable set. No artifact matching the task’s specification is present. The implementer must provide the actual implementation (e.g., function/module) and evidence (e.g., unit test, usage example) that the flagging behavior works as described.
- **T041** — No code, configuration, tests, or documentation implementing “Proxy Validated” logging for the condition r ≥ 0.5 is present; the only provided material concerns an unrelated curriculum scheduler feature, so the required artifact is missing.
- **T042** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_report.md
- **T044** — No documentation files were provided in the `docs/` directory, nor any text explaining the scheduler trace as required by task T044. The implementer’s claim lacks the actual updated documentation artifact, so the requirement is not satisfied.
