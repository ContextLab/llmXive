# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The pinned list embedded in `code/bootstrap.py` (`_REQUIREMENTS`: numpy/pandas/.../psutil, datasets, torch==2.2.0, opencv-python, tqdm) does NOT match the actual `requirements.txt` on disk (which instead lists huggingface_hub, ultralytics, detectron2, pingouin, ruff, black, python==3.11, etc.), so the task's own verification criterion — "the generated requirements.txt matches the pinned list" — fails; running bootstrap.py would overwrite the existing file with a different list. Additionally, there is no execution evidence that `bootstrap.py` was run and exited 0 printing the tree, and `quickst
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
