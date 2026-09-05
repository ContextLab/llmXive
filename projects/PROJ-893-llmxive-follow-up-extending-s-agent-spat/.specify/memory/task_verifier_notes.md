# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`code/`, `data/raw/`, `data/derived/`, `data/results/`, `specs/`, `tests/`) is present in the provided artifacts; the claim lacks any tangible evidence that the required folders were created.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012** — The `run_solver.py` script is incomplete (truncated) and never writes to the required `data/derived/predictions.jsonl` or `data/derived/latency_log.jsonl` files, which are absent from the repository. Consequently the task’s output artifacts are missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/results/benchmark_results.csv
- **T022** — declared artifact(s) missing/empty/invalid: data/results/failure_analysis_report.md
- **T026** — No execution logs, output JSON files, benchmark tables, or any other artifacts were provided to demonstrate that the full pipeline was run end‑to‑end and that all acceptance scenarios in `spec.md` were satisfied. The claim lacks concrete evidence such as solver run results, latency measurements, or statistical test outputs.
- **T027** — No code, script, test results, or documentation were provided to demonstrate that the solver input has been checked and confirmed to contain no VLM traces, as required by FR‑001 and FR‑002. The implementer must supply a concrete validation artifact (e.g., a verification script and its output/report) showing that all input files are free of VLM trace data.
