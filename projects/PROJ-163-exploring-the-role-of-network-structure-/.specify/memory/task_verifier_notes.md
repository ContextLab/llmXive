# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/fetcher.py exit=1
- **T002** — The required `data/processed/performance_metrics.csv` file does not exist, the `performance_metrics.schema.yaml` schema is missing, and the validation test `code/tests/test_processed_csv.py` fails (NameError due to missing import). Additionally, the suggested `code/process_raw.py` module is absent. These missing/incorrect artifacts prevent the task from being considered complete.
- **T003** — The repository lacks the required `code/tests/test_graph_builder.py` file (the test suite is present under `tests/` instead of the mandated path) and the existing tests fail – the edge‑betweenness mean assertion does not match the implementation. Moreover, the CLI run produces an empty `data/processed/graph_metrics.csv` (only the header) because no raw snapshots are found, violating the requirement for a non‑empty, schema‑valid metrics file. These issues must be fixed before the task can be considered complete.
- **T004** — Requested task execution failed; rerun successfully: code/generate_correlation_results.py exit=1
