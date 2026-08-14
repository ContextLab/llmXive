# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `code/utils/`, `tests/`, `data/raw/`, `data/processed/`) being present was provided; the claim lacks any artifact listing or file‑system snapshot confirming the project structure exists.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015** — The required schema file `contracts/interaction_schema.schema.yaml` is missing, and the provided `code/01_ingest.py` does not show any call to `validate_dataframe` (or similar) that would raise on invalid data. Consequently the ingestion script does not actually perform the hard‑gate validation against the specified schema.
- **T018** — The repository contains a `code/01_ingest.py` file, but its content is truncated and does not show a complete implementation that groups by `user_id`/`timestamp`, sorts chronologically, and writes the required CSV. Moreover, the expected output file `data/processed/valence_sequence.csv` is absent. Both the functional script and the required output artifact are missing, so the task is not satisfied.
- **T024** — The provided `code/02_metrics.py` expects `data/processed/valence_sequence.csv`, but that CSV file is absent from the repository, so the script cannot actually load and group the data as required. The missing input file prevents the task from being fulfilled.
