# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022** — Requested task execution failed; rerun successfully: code/download_il_benchmark.py exit=1; code/main.py exit=1
- **T024** — The output `data/processed/bulk_properties.csv` exists with the required `pair_id`, `density`, `viscosity` columns and matches the schema, but the task's mandated fallback source `data/raw/experimental_bulk_properties.csv` is MISSING, and the execution log shows the script instead read from `data/experimental_bulk_properties.csv` — a path not specified by the task and not confirmed to exist on disk. With no NIST API call evidenced (log says "No NIST API URL configured") and no verifiable source data, the provenance of the 20 rows of density/viscosity values cannot be confirmed against real exp
- **T001** — Requested task execution failed; rerun successfully: code/main.py exit=2
