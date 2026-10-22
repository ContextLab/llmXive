# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The test file imports `generate_batch`, `_write_jsonl`, and `_write_validation_metrics` from `code.graph_generator`, but the actual `code/graph_generator.py` defines none of these (it has `generate_set` and inline file-writing in `main()`), so the current test file cannot even import successfully — the recorded passing pytest log is stale relative to the current artifacts. Additionally, the key integration test `test_generated_dataset_integration` (schema + |r| < 0.2 on the generated dataset) was SKIPPED because `data/raw/synthetic_puzzles.jsonl` does not exist, so the task's core verification
- **T003** — Requested task execution failed; rerun successfully: code/graph_generator.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/rm_executor.py exit=1
