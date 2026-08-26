# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011b** — The provided `code/ingest.py` excerpt shows no implementation of the required date‑range check (min/max date logic, warning logging, or setting a `data_limitation` flag). Moreover, the required `results/metrics.json` file does not exist, so the flag cannot be recorded. Both the validation step and the metrics output are missing.
- **T013** — The repository contains `code/ingest.py`, but the visible portion shows no logic for downloading NOAA SWPC Dst indices or writing them to `data/raw/dst_indices.csv`. Moreover, the required output file `data/raw/dst_indices.csv` is absent, and the referenced schema file is also missing. The task’s core requirement—producing the Dst CSV file—is not met.
