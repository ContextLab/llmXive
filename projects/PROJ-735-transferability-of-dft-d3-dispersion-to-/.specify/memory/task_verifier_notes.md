# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022** — Requested task execution failed; rerun successfully: code/download_il_benchmark.py exit=1; code/main.py exit=1
- **T023** — The required verification artifacts `code/validation.log` and `data/processed/validated_metadata.csv` are both MISSING, so no validation of `data/raw/metadata.csv` (null `reference_energy` checks, `pair_id` uniqueness, omitted-record logging) has actually been performed or recorded. The implementer must run the validation and write both the log of omitted records and the cleaned CSV.
- **T024** — Requested task execution failed; rerun successfully: code/retrieve_bulk_properties.py exit=1
