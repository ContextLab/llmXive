# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008a** — The provided `code/01_data_ingestion.py` does not contain logic to download the ESOL CSV, validate the `smiles`/`logP` columns against the required schema, or perform the a‑priori power analysis and write `data/processed/power_analysis_report.json`. Moreover, the referenced schema file and the JSON report are absent from the repository.
- **T008c** — The required output files `data/processed/filtered_esol.csv` and `data/logs/large_molecule_exclusions.log` are absent, and the provided `code/01_data_ingestion.py` (as shown) does not contain any logic that filters molecules by molecular weight > 1000 Da or writes those files. The implementation therefore does not meet the task’s deliverables.
