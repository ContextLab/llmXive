# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `src/` directory contains a `utils/` subdirectory and `tests/` contains a `unit/` subdirectory, so they are not empty as required. Moreover, the verification script `tests/unit/test_skeleton.py` is missing, so the CI test that asserts the directories exist cannot run.
- **T004** — The evidence shows that `src/config/species.yaml` and `src/config/parameters.yaml` are marked **MISSING**, so the required configuration files do not exist at the specified location. Consequently the task’s core deliverable (the two YAML files with the prescribed keys and values) is not present, even though the unit‑test script happened to pass by looking in a different path. The missing YAML files must be added under `src/config/` with the correct structure for the task to be complete.
- **T005** — Requested task execution failed; rerun successfully: tests/unit/test_seed_flag.py exit=1
- **T006** — The required `species.yaml`, the populated `data/raw/` archives, the `data/artifact_hashes.yaml` file, and the unit test `tests/unit/test_geo_downloader.py` are all missing, so the script cannot be verified to download GEO series, skip those with <30 samples, or record checksums as the task demands.
- **T007** — Requested task execution failed; rerun successfully: code/src/pipeline/verify_samples.py exit=1
