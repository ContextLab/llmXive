# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The bootstrap script's pinned `_REQUIREMENTS` list (ultralytics, detectron2, pingouin, ruff, black, `python==3.11`) does not match the actual `requirements.txt` on disk (datasets, torch, opencv-python, huggingface_hub, no ruff/black/python pin), so the stated verification — "the generated requirements.txt matches the pinned list" — fails; running `bootstrap.py` would overwrite the correct file with a divergent (and invalid, e.g. `python==3.11`) list. Additionally, `quickstart.md` tells users to `pip install -r code/requirements.txt`, but the file lives at the project root, and there is no exec
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
