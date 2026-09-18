# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — The required file `contracts/target_decision.schema.yaml` is missing (no `schema.yaml` present), so no JSON schema has been provided. The task’s deliverable is absent, making the implementation incomplete.
- **T005a** — The required deliverable `data/raw/materials_project_data.json` is absent from the repository, and there is no evidence that `code/data/fetch_materials.py` was executed to produce it. Without this JSON file the task’s primary output is missing.
- **T005b** — The repository contains the `fetch_nist_data.py` script, but the required output file `data/raw/nist_data.json` is absent, indicating the script has not been executed (or its results were not saved). The deliverable specified by the task is therefore missing.
- **T005c** — The repository contains `code/data/target_consistency_check.py`, but the required output file `data/results/target_decision.json` is absent, and the provided script excerpt is truncated before any code that writes the JSON. Without the generated JSON (or evidence it is produced), the task’s deliverable is not satisfied.
- **T006a** — The required artifact `data/results/target_decision.json` does not exist on disk, so the deliverable is missing. The task’s core requirement—to verify and provide that file—has not been satisfied.
- **T006d** — declared artifact(s) missing/empty/invalid: data/results/data_manifest.json
- **T013** — The script `code/data/fetch_literature_pcm.py` exists and contains the fetching logic, but the required output file `data/external/literature_pcms_raw.csv` is missing, so the deliverable is not fully satisfied. The CSV must be generated and present.
- **T023a** — declared artifact(s) missing/empty/invalid: data/results/validation_config.json
