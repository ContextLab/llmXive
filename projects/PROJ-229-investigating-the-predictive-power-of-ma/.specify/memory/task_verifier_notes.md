# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005a** — The script `code/data/fetch_materials.py` is present, but the required output file `data/raw/materials_project_data.json` does not exist on disk, so the data retrieval step was not completed. The deliverable is missing.
- **T005b** — The required artifact `data/raw/nist_data.json` is absent; only the fetch script is present (and truncated), but there is no evidence that it was executed or that the JSON file was generated. The deliverable file must exist and contain the fetched NIST data for the task to be considered complete.
- **T005c** — The required `data/results/target_decision.json` file is missing, and the provided `target_consistency_check.py` script is truncated before performing the correlation calculation and writing the decision, so the implementation is incomplete.
- **T006d** — declared artifact(s) missing/empty/invalid: data/results/data_manifest.json
- **T006a** — The repository contains the `code/data/target_consistency_check.py` script, but the required output file `data/results/target_decision.json` is absent, and there is no evidence that the script was executed to generate it. Consequently, the deliverable specified by the task has not been produced.
- **T008a** — The `code/utils/checksum.py` script is present, but the required output file `data/checksums.txt` does not exist, so the task of recording the SHA256 checksums for the raw data files is not fulfilled.
- **T008b** — declared artifact(s) missing/empty/invalid: data/checksums.txt
- **T013** — The repository contains the required `code/data/fetch_literature_pcm.py` script, but the expected output file `data/external/literature_pcms_raw.csv` is absent. Without the CSV, the deliverable is not fully satisfied. The next implementer must ensure the script is executed (or otherwise provide the CSV) so that the file exists and contains the fetched literature PCM data.
- **T023a** — declared artifact(s) missing/empty/invalid: data/results/validation_config.json
