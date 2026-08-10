# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw`, `data/processed`, `data/results`, `data/external`) is provided; the implementer did not supply any file‑system listing, script output, or screenshots confirming their creation. The task remains undone until those directories exist and are shown.
- **T001b** — No evidence of the required directories (`code/data`, `code/models`, `code/utils`) is provided; the artifact list is empty, so the claim that the code directories were created cannot be verified.
- **T001c** — The claim provides no concrete evidence (e.g., a directory listing, screenshots, or file tree) that the required `tests/unit`, `tests/integration`, and `tests/contract` directories actually exist in the repository. Without such proof, we cannot verify that the task was completed.
- **T005a** — The `target_consistency_check.py` file is present but the shown code is truncated and does not demonstrate the Pearson correlation calculation or the JSON‑writing step required by the task. Moreover, the expected output file `data/results/target_decision.json` is absent, indicating the script either was not executed or does not create the required artifact. The implementer must ensure the script computes the correlation, decides the target, writes the result to the specified JSON file, and that the JSON file exists.
- **T006b** — The required file `contracts/target_decision.schema.yaml` does not exist (listed as missing), so no JSON schema has been provided. The task’s core artifact is absent.
- **T013** — declared artifact(s) missing/empty/invalid: data/external/literature_pcms_raw.csv
- **T013a** — declared artifact(s) missing/empty/invalid: data/results/target_decision.json, data/external/literature_pcms_mapped.csv, data/results/mapping_log.json
