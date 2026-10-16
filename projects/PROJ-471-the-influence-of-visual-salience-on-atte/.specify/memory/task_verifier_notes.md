# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The on-disk `requirements.txt` (huggingface_hub, opencv-python, torch, datasets, ultralytics, pingouin) does not match the pinned list in `code/bootstrap.py` (which pins `torch==2.2.0` and includes `detectron2`), so the task's own verification criterion — "the generated requirements.txt matches the pinned list" — fails; the historical log shows bootstrap once wrote the pinned file, but the current artifact contradicts it. Additionally, there is no execution evidence that the advertised entry point `python -m code.main --stage smoke` actually runs (only `bootstrap.py` exit 0 is recorded). Fix b
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/download_data.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/salience/generate_maps.py exit=1
