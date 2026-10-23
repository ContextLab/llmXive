# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/data/fetch_heas.py exit=1
- **T002** — The required input files `data/raw/heas_raw.csv` and `data/raw/elemental_properties.csv` are missing, and the unit‑test `code/tests/test_descriptors.py` is absent. Consequently the descriptor script cannot be exercised as specified, and the fallback to a hard‑coded property table violates the requirement to use the frozen CSV. The pipeline cannot produce the mandated `data/processed/hea_descriptors.csv` nor validate it against the contracts.
- **T003** — The validator script cannot locate the required schema because it looks for `contracts/hea_composition.schema.yaml` at the project root, while the actual file resides under `specs/.../contracts/`. This causes a `FileNotFoundError` and all three unit tests fail. Additionally, the default CSV at `data/input/compositions.csv` is missing, so the script would abort with a file‑not‑found error instead of validating missing fields. Fix the schema path (or move the schema) and provide the expected default CSV.
- **T016** — Requested task execution failed; rerun successfully: code/data/verify_dataset_presence.py exit=1
