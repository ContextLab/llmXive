# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The submission provides no evidence of the required `data/raw/`, `data/processed/`, or `data/adapters/` directories, nor any `.gitkeep` files within them. Without visible artifacts confirming these directories exist and contain the placeholder files, the task requirement is not satisfied.
- **T011** — The required integration test file `tests/integration/test_adapter_generation.py` is absent, and the expected adapter file `data/adapters/sample_adapter.safetensors` does not exist, so the task’s stated requirement is not met.
- **T016** — The provided evidence contains only the task description and project requirements, but lacks the actual `ast_parser.py` file or any code snippet demonstrating the implementation of the control-flow logic. Without seeing the file content, it is impossible to verify if the logic to skip malformed files, the specific logging calls using the T006 handler, and the `continue` statement for FR-007 are genuinely implemented rather than just described.
- **T017** — No evidence of a modified `adapter_generator.py` containing a RAM‑usage check that aborts when usage exceeds 7 GB and logs the required error (FR‑008) was provided. The artifact is missing, so the task is not verified as completed.
- **T018** — No evidence of a modified `adapter_generator.py` containing checkpoint validation logic is provided; the required code artifact is missing, so we cannot confirm that the abort‑on‑incompatible‑base‑model behavior was implemented.
- **T021** — The repository contains a partially implemented `runner.py`, but the provided excerpt stops before any scoring logic or CSV writing, and the required output file `data/results/ast_scores.csv` is missing. Consequently the task of computing exact‑match scores and saving them to the specified CSV has not been fulfilled.
- **T022** — declared artifact(s) missing/empty/invalid: data/results/latency.csv
- **T031a** — declared artifact(s) missing/empty/invalid: data/results/baseline_score.json
- **T033** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_summary.csv
- **T049a** — declared artifact(s) missing/empty/invalid: data/results/baseline_generation_latency.json
- **T049b** — declared artifact(s) missing/empty/invalid: data/results/generation_latency_comparison.json
- **T050** — declared artifact(s) missing/empty/invalid: data/results/memory_log.csv, data/results/resource_summary.csv
- **T052** — declared artifact(s) missing/empty/invalid: scripts/validate_quickstart.sh
