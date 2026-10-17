# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — `code/main.py` exists and its content genuinely implements the generate → compress → analyze orchestration with loud schema-validation failures, and the `--help` run is evidenced (exit 0, all flags documented). However, the task's other two verification requirements have no execution evidence: there is no record of a smoke run (`python code/main.py --generate --compress --analyze --n-workflows 20` exiting 0) and no record of `pytest` under `code/` passing — the only historical execution is the 0.1s help invocation. Additionally, the `data/results/` artifacts (e.g. `run_metrics.json` with durat
- **T111** — Requested task execution failed; rerun successfully: code/main.py exit=1
