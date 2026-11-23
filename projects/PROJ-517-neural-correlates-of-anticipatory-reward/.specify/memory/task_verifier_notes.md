# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — The required `state/dataset_candidates.json` file is not present, and no JSON content showing a verified OpenNeuro dataset URL, dataset ID, or the exact search query is provided. Consequently the task’s core deliverable—identifying and recording a reachable dataset candidate—is missing.
- **T000b** — No `state/dataset_candidates.json` file showing the required `verified` flag and `missing_columns` list was provided, nor any evidence of metadata fetching and column checks. The task’s core output is missing.
- **T000c** — No `state/dataset_candidates.json` was examined, and no `state/claim_status.json` was created or shown to contain the required status field. The implementer provided no code, script, or output demonstrating the time‑resolved analysis check, so the task’s required artifact is missing.
- **T000d** — No artifact containing the required statistical strategy definition was provided—there is no in‑memory or temporary configuration specifying the dispersion formula (deviance/df), the permutation test iteration count (≥ 1000), or the alpha level (0.05). The task therefore remains undone.
- **T002b** — declared artifact(s) missing/empty/invalid: projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt
- **T003a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005a** — The repository contains `code/synthetic_generator.py`, but the file is truncated and does not clearly show that it generates a flat‑float column `spike_time_ms` via a Poisson process with λ=50 Hz and seed 42. Moreover, the required schema file `contracts/dataset.schema.yaml` is missing, so the generator cannot be verified against the contract. The missing schema and incomplete implementation prevent the task from being considered fulfilled.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T018** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009b** — The repository lacks the required contract files `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`, so the test cannot actually validate them. Moreover, the provided `tests/contract/test_schemas.py` is truncated and does not contain a complete `test_schemas_validates` implementation. Both the artifact and its content are missing/unfinished, so the task is not genuinely completed.
