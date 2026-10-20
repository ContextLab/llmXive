# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `data/processed/` directory is missing, and the verification artifact `results/structure_report.txt` was never generated, so there is no evidence that `python -m compileall code/` exited 0 or that the full directory tree was confirmed. The implementer must create `data/processed/` and run the verification commands to produce the structure report listing all expected directories.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
