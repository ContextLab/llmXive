# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T057** — The script `code/utils/final_title_audit.py` is present but the provided excerpt shows no code that writes `data/results/title_audit.json` or exits with code 1 on a violation. Moreover, the required output file `data/results/title_audit.json` is missing entirely. The task’s core output and exit‑code behavior are therefore not satisfied.
- **T058** — The script `code/utils/methodology_consistency_check.py` exists, but the provided code (truncated) never writes the warnings to `data/results/methodology_consistency.json`, and that JSON file is absent from the repository. Consequently the required output artifact is missing, so the task is not fully satisfied.
