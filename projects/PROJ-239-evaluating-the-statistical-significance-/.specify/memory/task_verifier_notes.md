# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014** — declared artifact(s) missing/empty/invalid: data/derived/baseline_results.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/derived/robustResults.csv
- **T023** — No artifact showing a `config.py` file with a defined `ALPHA_LEVELS` default was provided; without the file content we cannot verify that the required constant exists. The implementer must supply the `config.py` source containing the `ALPHA_LEVELS` definition.
- **T025** — declared artifact(s) missing/empty/invalid: data/derived/final_report.csv
- **T027** — The provided `timing.csv` and `memory.csv` contain only header rows and no logged measurements, and the visible portion of `code/simulation_runner.py` does not show any console timing output, CSV appends, or an explicit error raise when peak memory exceeds 7 GB. Consequently the required performance‑monitoring behavior is missing.
- **T032** — No test run output, exit code, or updated `quickstart.md` file is provided; the required artifacts to prove the quickstart validation were completed are missing.
- **T035** — The repository contains `code/uci_ingest.py`, but the required output file `data/raw/uci_online_retail.csv` is absent, and `data/checksums.txt` only holds a placeholder string instead of an actual SHA‑256 checksum. Consequently the ingestion, checksum generation, and PII‑scan steps have not been realized.
