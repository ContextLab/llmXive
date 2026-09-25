# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012c** — The required output file `data/filtered_swe_bench_v1.parquet` does not exist, and the provided `loader.py` snippet is truncated with no visible implementation of the graph‑traversal line‑count filtering or parquet writing. Consequently the task’s core requirements are not satisfied.
- **T017b** — The required artifact `data/intermediate/baseline_run.jsonl` is missing, so no annotations or fallback handling can be verified. The task’s core output does not exist.
- **T023** — The repository lacks the required `data/intermediate/hf_run_1b.jsonl` file (it is missing) and the `execution_result.schema.yaml` needed for validation. Moreover, the provided `run_high_fidelity.py` does not show an implemented `run_strategy()` function (the file is truncated and no such function is present). These missing artifacts mean the task’s requirements are not satisfied.
- **T027** — declared artifact(s) missing/empty/invalid: data/intermediate/hf_run_7b.jsonl, schema.yaml
- **T028** — declared artifact(s) missing/empty/invalid: data/results.csv
- **T030c** — declared artifact(s) missing/empty/invalid: data/results/comparison_report.md
- **T039** — declared artifact(s) missing/empty/invalid: data/results.csv, data/intermediate/baseline_run.jsonl, state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml
