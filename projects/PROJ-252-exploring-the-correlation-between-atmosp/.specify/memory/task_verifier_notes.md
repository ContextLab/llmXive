# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — `requirements.txt` is not frozen — it lists bare package names (numpy, pandas, scipy, …) with no pinned versions, directly violating the "pin dependencies / frozen" requirement. Additionally, `docs/quickstart.md` instructs running `python code/seed_init.py` to print "Pipeline completed successfully" and produce `logs/seed_initialization.log`, but there is no evidence that `code/seed_init.py` exists or that the command was executed (no log file, no run output), and no evidence that `pip install -r requirements.txt` succeeded.
- **T002** — Requested task execution failed; rerun successfully: code/download.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
