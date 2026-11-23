# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `code/requirements.txt` exists but pins `pandas==2.1.3` and `rdkit==2023.9.4`, contradicting the task's required `pandas==2.1.4` and `rdkit==2023.9.5`. Additionally, there is no evidence (log/output) that `pip install -r code/requirements.txt --dry-run` was executed to verify the installation.
- **T005** — `code/utils/logger.py` exists and mostly matches the requirement (file + stdout handlers, `code/logs/app.log`), but it references `sys.stdout` in the console handler without importing `sys`, so calling `setup_logger()` raises a `NameError` — the function cannot actually run. Fix by adding `import sys` (or using `logging.StreamHandler()` defaulting to stderr/stdout).
- **T023** — Requested task execution failed; rerun successfully: code/analysis/merge.py exit=1
