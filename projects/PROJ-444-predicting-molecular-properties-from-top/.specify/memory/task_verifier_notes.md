# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/01_data_ingestion.py exit=1
- **T014** — The required input `data/raw/esol.csv` is MISSING, and the test works around this by silently materializing a different dataset (skfp lipophilicity) in its place — that is a fabricated stand-in, not the ESOL data the schema contract describes, and it would mask the missing artifact rather than validate it. Additionally, there is no execution evidence that `pytest code/tests/test_dataset_schema.py` actually passes (no test output, and the test depends on the skfp package being installed). The implementer must provide the real `data/raw/esol.csv` (ESOL solubility data with the schema's columns),
- **T002** — Requested task execution failed; rerun successfully: code/02_tda_computation.py exit=1
