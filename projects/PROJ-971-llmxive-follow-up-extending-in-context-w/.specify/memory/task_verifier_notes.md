# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The task requires actually running `run_end_to_end.py --subset 50` and producing a printed 50-row summary table, but the evidence contains only source files — no execution output, no generated `data/raw/clip_*.npz` files, no `data/processed/descriptors.csv` or `data/descriptors_subset.csv`, and no run log, so there is no proof the pipeline ever ran or that the table was printed. Additionally, there are two divergent copies of `generate_clips.py` and `extract_descriptors.py` (`code/src/pipeline/` vs `src/pipeline/`), and the `code/src` extract_descriptors version depends on a schema file (`spec
- **T007** — Requested task execution failed; rerun successfully: scripts/run_minimal.sh exit=1
- **T005** — Requested task execution failed; rerun successfully: code/src/pipeline/grid_search_labels.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/src/pipeline/train_regressor.py exit=1
- **T016** — The test `code/tests/test_descriptor_schema.py` exists, but it raises a `FileNotFoundError` because the required schema file `specs/001-auto-icwm-latent-dynamics/contracts/descriptor.schema.yaml` is missing, causing pytest to fail. The missing schema file must be added (or the path corrected) and the test must pass for the task to be considered complete.
