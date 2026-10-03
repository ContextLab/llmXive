# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/`, `tests/`, `data/`, `results/`, `data/raw`, `data/processed`, `state`) is provided; the claim lacks any artifact showing that the `mkdir -p` command was executed and the structure exists. The implementer must supply a view of the repository (e.g., a directory listing or screenshots) confirming that all specified folders are present.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or similar) were provided or referenced, and there is no evidence of ruff/black being set up in the repository. The required artifacts to demonstrate that linting and formatting tools are configured are missing.
- **T006** — declared artifact(s) missing/empty/invalid: src/data_models.py
- **T005a** — declared artifact(s) missing/empty/invalid: src/loader.py
- **T005b** — declared artifact(s) missing/empty/invalid: results/descriptive_stats.json
- **T005c** — declared artifact(s) missing/empty/invalid: state/data_availability.yaml
- **T005d** — No evidence of a `logs/warning.log` file was provided, nor any output showing the required warning message when the file count in `data/raw/` is below 10. The implementer did not supply the artifact needed to verify the task.
- **T007** — declared artifact(s) missing/empty/invalid: src/utils.py
- **T010** — The `tests/test_topology.py` file exists and defines the first two required test functions, but the repository lacks `src/topology.py`, so the import `from src.topology import compute_metrics` will fail and the tests cannot be executed. Additionally, the displayed snippet truncates the `test_path_length_disconnected_graph` implementation, leaving it unclear whether that test is fully realized. The missing source module (and possible incomplete third test) must be added/fixed for the task to be truly complete.
- **T011** — The repository lacks the required `src/simulation.py` file, so the imported functions cannot be tested. Moreover, the `tests/test_simulation.py` file does not contain the specific test cases `test_ring_graph_analytical_match_5pct` and `test_bisection_search_logic` that the task demanded. Both the implementation file and the exact unit tests are missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/topology.py
- **T014** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T015** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T016** — declared artifact(s) missing/empty/invalid: results/sim_results.json
- **T017b** — declared artifact(s) missing/empty/invalid: results/sim_results.json, results/verification_report.json, results/manual_verification_log.csv
- **T030** — declared artifact(s) missing/empty/invalid: results/pipeline_status.json
- **T022** — The required output files `results/sim_results.json` and `data/processed_metrics.csv` are both missing, and no evidence of updated `main.py` logic is provided. Without these artifacts, the aggregation and regression trigger cannot be verified.
- **T025** — declared artifact(s) missing/empty/invalid: src/stats.py, data/processed_metrics.csv, results/descriptive_stats.json, state/data_availability.yaml
- **T023a** — declared artifact(s) missing/empty/invalid: src/stats.py
