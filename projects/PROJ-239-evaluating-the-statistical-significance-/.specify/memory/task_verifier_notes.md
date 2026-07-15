# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: data/derived/baseline_results.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/derived/robustResults.csv
- **T023** — No artifact showing a `config.py` file with a defined `ALPHA_LEVELS` default was provided; without the file content we cannot verify that the required constant exists. The implementer must supply the `config.py` source containing the `ALPHA_LEVELS` definition.
- **T025** — declared artifact(s) missing/empty/invalid: data/derived/final_report.csv
- **T027** — The provided `simulation_runner.py` defines `log_timing` (which appends to `data/timing.csv`) and a `downsample_clusters` function, but the snippet ends before a complete `log_memory` implementation, and there is no visible code that prints wall‑clock time to the console or raises an error when peak memory exceeds 7 GB. Moreover, `data/timing.csv` and `data/memory.csv` contain only headers and no logged entries, indicating the logging functionality was not fully realized. The missing console output, memory‑logging logic, and memory‑limit error handling must be added.
- **T032** — No test run output, exit code, or updated `quickstart.md` file is provided; the required artifacts to prove the quickstart validation were completed are missing.
- **T035** — The `code/uci_ingest.py` script exists, but the required output files are absent: `data/raw/uci_online_retail.csv` is missing, and `data/checksums.txt` contains only a placeholder rather than a real SHA‑256 checksum. Without these artifacts the ingestion, checksumming, and PII‑scan requirements are not satisfied.
