# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T002c** — The repository lacks the required `contracts/dataset.schema.yaml` file, so the validator cannot load the pre‑existing schema. Moreover, the provided `schema_validator.py` is truncated (e.g., `_validate_column_types` is incomplete) and does not fully implement the validation logic or error‑code handling. Both the missing schema and incomplete code prevent the task from being genuinely fulfilled.
- **T008** — The repository lacks both a `conftest.py` with pytest seed‑pinning configuration and a `results/checksums.txt` file. Moreover, `code/01_download_data.py` does not contain any code that writes the computed SHA‑256 checksum to `results/checksums.txt` before exiting. These missing artifacts mean the task’s explicit requirement is not satisfied.
- **T010** — The required artifact `data/raw/wesad/WESAD.zip` is missing, so the download step was not performed and the script’s error‑handling behavior cannot be verified. The task’s core requirement (having the ZIP file at the specified path) is not satisfied.
- **T010b** — declared artifact(s) missing/empty/invalid: data/raw/openneuro/index.json
