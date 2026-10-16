# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T101** — The required verification artifact `results/structure_report.txt` exists but is 0 bytes (sha256 of empty file), so it does not list any directories, let alone all expected ones. The only execution record is `setup_skeleton.py` exiting 0; there is no evidence that `python -m compileall code/` was run or that the `find . -type d | sort > results/structure_report.txt` verification command was executed. The implementer must regenerate the structure report (non-empty, listing all expected directories) and record a successful compileall run.
- **T103** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
