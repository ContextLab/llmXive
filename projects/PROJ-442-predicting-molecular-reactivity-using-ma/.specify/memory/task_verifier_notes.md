# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The repository contains a non‑empty `src/modeling/config.yaml`, but there is no accompanying script, module, or function shown that reads this file (e.g., using `yaml.safe_load`) as required by the task “load `config.yaml` from `src/modeling/config.yaml`”. The loading logic is missing.
- **T013** — The repository lacks the required `config.yaml` containing the SMARTS patterns, and the shown `src/utils/chemistry.py` is truncated and does not include a complete implementation (e.g., a function that actually classifies a reaction SMILES into “SN1”, “SN2”, or “Diels‑Alder”). Both essential artifacts are missing or incomplete, so the task is not satisfied.
- **T016** — No code, script, or modified CSV file was presented showing the added logic to count samples per class, log warnings for classes with fewer than 1,000 rows, and physically remove those rows from the output. The required artifact is missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/filtered_reactions.csv
