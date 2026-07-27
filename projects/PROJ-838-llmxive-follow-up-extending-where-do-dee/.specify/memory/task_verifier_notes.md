# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T023** — The `process_batch` implementation in `code/metrics.py` is cut off (`output_file = Path(outpu`), so it never writes the CSV. Consequently `data/processed/metrics.csv` does not exist, and the integration test cannot pass. The required batch logic and output file are missing.
- **T029** — The `stratified_split` function in `code/evaluator.py` is truncated (ends with `save_metrics(train_df` and never saves the test set or returns the DataFrames). Additionally, the required input file `data/processed/metrics.csv` and the expected output files `data/processed/train_metrics.csv` and `data/processed/test_metrics.csv` are missing. The unit test is present, but the core implementation and required data artifacts are incomplete.
