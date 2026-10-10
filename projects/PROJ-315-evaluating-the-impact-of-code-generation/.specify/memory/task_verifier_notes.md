# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The integration test file `tests/integration/test_data_completeness.py` exists, but it imports `main` from `code/data/preprocess.py`, which implements an audit‑accuracy pipeline and never performs a data‑completeness check. Consequently the test cannot trigger the required `ValueError`, and it does not assert that the error message contains the exact phrase “Data Completeness Error”. The test therefore does not satisfy the task’s requirement.
- **T011** — The `tests/integration/test_power_check.py` file exists and raises a `ValueError` when a group size is < 500, but the asserted error message only contains “Power insufficiency” and does not include the required phrase “Power Insufficiency Error”. The test therefore does not verify the exact message stipulated by the task.
- **T012** — The provided `code/data/fetch.py` calls `load_dataset` without the required `batch_size=1000` argument and then materialises the entire streaming dataset into a list/DataFrame, which defeats the memory‑efficient chunked streaming requirement. It also does not implement chunked processing of the full dataset as specified. The task’s core requirement is therefore not satisfied.
- **T017a** — Requested task execution failed; rerun successfully: code/data/generate_audit_sample.py exit=1
- **T032** — declared artifact(s) missing/empty/invalid: code/analysis/viz.py, docs/reports/boxplot_comment_count.png, docs/reports/boxplot_sentiment.png, docs/reports/boxplot_merge_time.png
- **T033** — declared artifact(s) missing/empty/invalid: code/analysis/viz.py, docs/reports/histogram_comment_count.png, docs/reports/histogram_sentiment.png
- **T037** — declared artifact(s) missing/empty/invalid: docs/research.md, docs/quickstart.md
- **T041a** — declared artifact(s) missing/empty/invalid: code/benchmark/run_time.py
