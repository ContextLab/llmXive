# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/data/download.py` script exists but the unit test fails because the specified Hugging Face dataset (`molecule-net/permeability`) cannot be loaded, so no raw CSV is written and `data/raw/` remains empty. Consequently `data/raw/checksums.json` is missing, and the loader does not demonstrate successful fetching of a real permeability dataset nor the required checksum recording.
- **T002** — Checked `code/data/preprocess.py` – it implements `MoleculeProcessor.process` but aborts with `SystemExit` when the retention rate is below the hard‑coded 95 % threshold, causing the unit test `test_preprocess_writes_output` to fail and leaving `data/processed/processed_data.csv` absent. The required output file is missing and the processing routine does not reliably produce it as specified.
- **T004** — Requested task execution failed; rerun successfully: code/models/rf_ablation.py exit=1
