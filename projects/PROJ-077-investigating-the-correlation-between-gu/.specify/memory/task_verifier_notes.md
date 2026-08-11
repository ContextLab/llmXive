# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T054** — No updated README.md file is provided; there is no evidence that explicit instructions for obtaining UK Biobank data, the required placement in data/raw/, or the specific microbiome, cognitive, and dietary fields have been added. The required documentation artifact is missing.
- **T014a** — The provided `code/data_ingestion.py` only defines helper functions (`check_dqs_availability`, `calculate_dqs`) and does not contain any logic that checks for the presence of `data/raw/dietary_data.csv` (or required columns) and raises a fatal error when it is missing. Moreover, the required `dietary_data.csv` file is absent from the repository. The task’s core requirement—implementing a file/column existence check with a fatal error—is therefore not satisfied.
