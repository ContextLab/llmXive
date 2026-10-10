# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directory skeleton, `requirements.txt` (contains torch), `code/config.py`, and `quickstart.md` all exist, but the required quick-start command `python code/main.py --phase init` cannot succeed: `main.py`'s `run_init_phase` accesses `cfg.code_dir`, `cfg.tests_dir`, and `cfg.project_root`, none of which are defined in the shown `code/config.py` (it only defines `raw_data_dir`, `processed_data_dir`, `seed`, and two path properties), so it would raise `AttributeError` before printing "Initialization complete". Additionally, the quickstart.md instructs `python code/main.py --mode full`, which t
- **T002** — Requested task execution failed; rerun successfully: code/data/download_coco.py exit=1; code/data/download_diverse_prompts.py exit=1; code/data/preprocess.py exit=1
