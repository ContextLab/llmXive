# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007a** — No download script, checksum validation code, or resulting `data/raw/ctu13_scenario_*.csv` files are present; the implementer provided only a textual description of the intended logic, without any actual artifact that attempts the fetch, verifies the hash, writes the CSVs, or triggers the fallback task. Consequently the required output does not exist.
- **T007b** — declared artifact(s) missing/empty/invalid: data/raw/bot-iot_v3.csv
- **T009** — The required output files `data/processed/train_split.csv`, `data/processed/test_split.csv`, and `data/processed/graph_train_split.graphml` are absent from the repository, so the temporal holdout split and graph construction have not been performed. No other artifacts were provided to demonstrate that the split logic or graph creation was executed.
- **T008d** — declared artifact(s) missing/empty/invalid: data/processed/train_split.csv
