# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/fetcher.py exit=1
- **T002** — The required `data/processed/performance_metrics.csv` file does not exist, and the referenced `performance_metrics.schema.yaml` schema file is also missing, so the CSV cannot be validated nor does the test suite pass.
- **T003** — The recorded pytest run for `code/tests/test_graph_builder.py` FAILED (exit 1): `test_build_coupling_graph_path` fails because degree assortativity of the 3-node path is -1.0, not the asserted -0.5 (the test's expectation is wrong for a P3 graph). Additionally, `data/processed/graph_metrics.csv` is MISSING, so there is no evidence the CLI was run to produce the required output, and the CLI accepts `--output` rather than the specified `--out` flag. Fix the test's expected assortativity (or the metric), add the `--out` alias, and run the CLI to generate the non-empty CSV.
- **T004** — Requested task execution failed; rerun successfully: code/generate_correlation_results.py exit=1
