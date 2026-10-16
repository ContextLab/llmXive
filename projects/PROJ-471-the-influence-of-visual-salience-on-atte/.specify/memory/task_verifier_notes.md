# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The recorded execution of `code/tests/test_bootstrap.py` failed (exit 1, `AttributeError: property 'root' of 'ProjectPaths' object has no setter`), so there is no evidence that `bootstrap.py` runs successfully, prints the tree, and exits 0. Moreover, the pinned list embedded in `bootstrap.py` (`_REQUIREMENTS`: torch==2.2.0, torchvision, detectron2, ultralytics, pingouin, ruff/black, `python==3.11`, etc.) does not match the actual root `requirements.txt` (numpy/pandas/scipy unpinned, requests, jsonschema, tqdm, no detectron2/ultralytics), so the "generated requirements.txt matches the pinned li
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
