# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — `requirements.txt` is not frozen: it lists bare package names (pandas, numpy, scipy, etc.) with no pinned versions, directly contradicting the task's requirement to pin dependencies — and `docs/quickstart.md` falsely claims "all versions are pinned/frozen." The quickstart command (`python code/seed_init.py`) does have execution evidence (exit 0, "Pipeline completed successfully", seed log written), and `code/__init__.py` correctly sets both seeds to 42, but there is no evidence that `pip install -r requirements.txt` succeeded without warnings. Fix by pinning exact versions in `requirements.txt
- **T002** — Requested task execution failed; rerun successfully: code/download.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
