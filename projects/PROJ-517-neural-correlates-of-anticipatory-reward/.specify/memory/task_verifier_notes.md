# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000a** — The required `state/dataset_candidates.json` file is not present, and no JSON content showing a verified OpenNeuro dataset URL, dataset ID, or the exact search query is provided. Consequently the task’s core deliverable—identifying and recording a reachable dataset candidate—is missing.
- **T000d** — No artifact containing the required statistical strategy definition was provided—there is no in‑memory or temporary configuration specifying the dispersion formula (deviance/df), the permutation test iteration count (≥ 1000), or the alpha level (0.05). The task therefore remains undone.
- **T002b** — declared artifact(s) missing/empty/invalid: projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt
- **T003a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — The required output file `data/raw/synthetic_test.csv` is absent, and the provided `synthetic_generator.py` does not clearly produce the specified flat columns (`spike_time_ms`, `snr`, `isolation_distance`) nor write the CSV at the expected path. Additionally, the referenced schema file is missing. These gaps mean the task’s deliverables are not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T018** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009b** — The `tests/contract/test_schemas.py` file exists but the required schema files (`contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`) are missing, so the test cannot actually validate anything. Additionally, the test function `test_schemas_validates` is not present in the shown code. The implementation therefore does not meet the task’s requirement.
- **T010** — The integration test file is truncated and never asserts `spike_count.sum() == expected_total`; it only checks row count. Moreover, `code/ingestion.py` ends abruptly (`df = df.d`) indicating a syntax error and missing implementation, so the pipeline cannot reliably produce the required DataFrame. The synthetic CSV is not present on disk (though the test tries to generate it), but the test itself is incomplete and the ingestion code is broken.
