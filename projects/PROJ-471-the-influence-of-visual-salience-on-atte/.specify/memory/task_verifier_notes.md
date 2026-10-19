# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The dataset `data/raw/ds003123/` is MISSING and `data/raw/checksums.json` contains an empty manifest (`{"files": []}`), so no real checksums were ever recorded. Worse, `verify_data.py` ends with `shutil.rmtree(dataset_dir)`, deleting the dataset after a successful verification — a destructive bug that explains why the directory is gone and makes the script unusable for its stated purpose. There is also no execution evidence (no test run output) that the success or DATA_MISSING_001 paths actually passed.
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
- **T004** — The `segment_roi.py` script imports `detectron2` at module load time, causing an import error (ModuleNotFoundError) and preventing the test suite from being collected or run. Consequently no masks, metadata, or CSV files are generated, and the required verification tests cannot pass. The missing `detectron2` dependency must be installed or the script must handle its absence gracefully for the task to be considered complete.
- **T005** — Requested task execution failed; rerun successfully: code/eye_tracking/parse_fixations.py exit=1
