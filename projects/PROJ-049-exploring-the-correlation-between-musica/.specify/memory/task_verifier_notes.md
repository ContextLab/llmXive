# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows that `data/raw/`, `data/processed/`, and `logs/` directories are missing (they are reported as MISSING), so the required project layout is not fully created.
- **T002** — The `requirements.txt` file exists and correctly pins exact versions for all listed packages, but there is no evidence that the required verification step was performed—no `installed.txt` file, no `pip freeze` command output, and no `diff -u` results showing that the installed environment matches the pinned versions. The implementer must provide the execution evidence of the verification command.
- **T004** — Requested task execution failed; rerun successfully: code/power_analysis.py exit=1
