# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The repository lacks the required `data/processed/metrics.csv` file, so the incremental write step is not present. Moreover, the provided `code/main.py` excerpt does not show the chunked processing loop that batches `fetch_molecules()` and writes results to the CSV, indicating the core functionality is missing. The next implementer must add the loop, ensure it respects `CHUNK_SIZE`, and create/write the `metrics.csv` with the specified columns.
- **T040** — The required `data/processed/metrics.csv` file does not exist, and the provided `code/main.py` excerpt shows no implementation that loads this CSV into a DataFrame (or handles `FileNotFoundError`). Both the necessary artifact and the specific loading logic are missing.
