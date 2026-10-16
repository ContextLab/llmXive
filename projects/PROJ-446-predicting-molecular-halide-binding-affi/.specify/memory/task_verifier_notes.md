# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The pipeline script never performs the required web‑fetch (no `requests` calls, no delay/back‑off, no HTML/JSON parsing) and instead reads a pre‑made `raw_scrape.json`. It also falls back to simulated data when host count < 50, violating the “must raise on fetch failure, no synthetic fallback” rule. The generated CSVs lack the required columns (`halide_identity`, `binding_constant`, `source`) and the required test file `code/tests/test_data_ingestion.py` is missing. The cleaning logic does not handle duplicate host‑halide averaging or logging of excluded records.
