# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — `requirements.txt` and `code/seed_init.py` match the spec (all pins present, seeds set to 42, log line written), but `docs/quickstart.md` does not contain the required single quick-start command `pip install -r requirements.txt && python -m code.seed_init && python -m code.main` — it instead documents a multi-step pipeline (`python code/download.py`, `preprocess.py`, etc.) and never mentions `seed_init` at all. Additionally, there is no evidence `logs/seed_initialization.log` was ever created (no run/execution evidence), and the seed script relies on `paths.path` without ensuring the `logs/` d
- **T002** — Requested task execution failed; rerun successfully: code/download.py exit=1
