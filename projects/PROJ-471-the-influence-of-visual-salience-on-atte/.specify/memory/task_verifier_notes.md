# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/ingestion/verify_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
- **T006** — The `code/analysis/feature_gen.py` script exists, but the required output file `data/interim/low_level_features.json` is missing, and the provided test suite fails during setup because `get_paths()` does not expose a `raw_data` attribute or a callable `raw` as the test expects. Moreover, the script’s scene‑complexity step unconditionally imports Detectron2, which is not guaranteed to be installed in the test environment, causing a runtime error before any JSON can be written. The implementation must (1) expose the raw‑data location in a way the test can discover, (2) handle missing Detectron2
- **T007** — Requested task execution failed; rerun successfully: code/analysis/align_data.py exit=1
- **T008** — Requested task execution failed; rerun successfully: code/analysis/collinearity_and_modeling.py exit=1
