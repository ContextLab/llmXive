# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file system evidence were provided showing that the required `src/`, `tests/`, `data/`, and sub‑directories (config, sim, retrieval, conditions, analysis, data/raw, data/derived, tests/contract, tests/integration, tests/unit, state, docs) actually exist. Without such artifacts, the claim that the project structure was created cannot be verified.
- **T007a** — The repository contains a partially‑implemented `src/sim/validation.py`, but the code is truncated before it writes the JSON and returns a checksum, and there is no `data/raw/ground_truth_raw.json` file on disk. Consequently the required artifact is not present and the implementation does not demonstrably fulfill the task.
- **T010** — declared artifact(s) missing/empty/invalid: src/data/stream_utils.py
- **T036a** — The `src/analysis/power_analysis.py` file exists but is incomplete/truncated and does not produce the required `data/derived/power_analysis_report.json`. The JSON report file is missing, so the task’s output artifact is not present.
- **T011** — The test file `tests/contract/test_trajectory_schema.py` is present but truncated and lacks a concrete test function that actually invokes `generate_baseline_failures` and validates the schema. Moreover, the required module `src/sim/trajectory_generator.py` does not exist, so the test cannot be imported or executed. The task’s deliverable—a working contract test for the generator’s output—is therefore missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py
- **T014** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py
- **T016** — declared artifact(s) missing/empty/invalid: data/raw/baseline_failures.json
- **T017** — declared artifact(s) missing/empty/invalid: data/raw/excluded_log.json
- **T018** — The `src/sim/validation.py` file does not contain any function that loads and cross‑references `data/raw/baseline_failures.json` with `data/raw/ground_truth_raw.json`; it only defines checksum and ground‑truth saving utilities. Moreover, both required JSON files are absent from the repository. Consequently the task’s core requirement is not satisfied.
- **T018a** — declared artifact(s) missing/empty/invalid: src/sim/trajectory_generator.py
- **T021** — declared artifact(s) missing/empty/invalid: src/conditions/degraded.py
- **T022a** — declared artifact(s) missing/empty/invalid: src/conditions/run_intervention.py, data/raw/intervention_failures.json
- **T023** — The required file `src/retrieval/relevance_scorer.py` does not exist in the repository, so the integration cannot be verified. The task demands a concrete implementation that calculates relevance scores, which is missing.
