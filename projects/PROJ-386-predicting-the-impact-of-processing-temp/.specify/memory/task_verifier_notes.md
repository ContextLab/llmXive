# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T049** — The `code/data/ingestion.py` file is truncated and does not contain the required `accumulate_streaming_stats` function (or any logic updating means/null counts). The generated `streaming_stats.json` shows all zeros and a row count of 0, indicating no real aggregation was performed. Additionally, the verification dataset `data/raw/test_sample.csv` is missing, so the tolerance check cannot be run.
