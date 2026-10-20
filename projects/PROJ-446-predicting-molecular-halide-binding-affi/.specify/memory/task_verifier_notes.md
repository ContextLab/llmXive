# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — All four required output artifacts (`data/raw/fetch_outcome.json`, `raw_scrape.json`, `raw_scrape_cleaned.csv`, `filtered_hosts.csv`) are MISSING, so there is no evidence the script was ever run or exits 0. Additionally, `fetch_pubchem_records` substitutes XLogP3 values as "binding constants" with a hard-coded solvent "acetonitrile" — a fabricated stand-in for real halide-binding measurements, which the task explicitly forbids — and the tests lack the required zero-records/exit-0 path coverage.
