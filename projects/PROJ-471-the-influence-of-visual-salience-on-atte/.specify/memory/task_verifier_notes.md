# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The repository contains `code/bootstrap.py`, `requirements.txt`, `quickstart.md`, and the unit test, but the required top‑level `logs/` directory is not present in the project tree. Without this directory the bootstrap script does not fully satisfy the layout requirement. Adding the missing `logs/` folder (and ensuring the script creates it) will resolve the issue.
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
- **T004** — The `segment_roi.py` script imports `detectron2` at module load time, causing an import error (ModuleNotFoundError) and preventing the test suite from being collected or run. Consequently no masks, metadata, or CSV files are generated, and the required verification tests cannot pass. The missing `detectron2` dependency must be installed or the script must handle its absence gracefully for the task to be considered complete.
- **T005** — Requested task execution failed; rerun successfully: code/eye_tracking/parse_fixations.py exit=1
