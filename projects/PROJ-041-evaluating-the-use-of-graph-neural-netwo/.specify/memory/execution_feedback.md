# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/data/download_ctu13.py (rc=1)

## Failing / missing run-book commands

- python code/data/download_ctu13.py -> rc=1

2026-10-16 13:14:57,998 INFO __main__: Attempting to download CTU‑13 Scenario 1 ZIP from https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1.zip
2026-10-16 13:14:58,131 WARNING __main__: URL https://www.stratosphereips.org/datasets-ctu13/CTU-13-Dataset/Scenario1/Scenario1.zip returned status 404
2026-10-16 13:14:58,131 INFO __main__: Attempting to download CTU‑13 Scenario 1 ZIP from https://www.stratosphereips.org/datasets-ctu13/Scenario1/Scenario1.zip
2026-10-16 13:14:58,254 WARNING __main__: URL https://www.stratosphereips.org/datasets-ctu13/Scenario1/Scenario1.zip returned status 404
2026-10-16 13:14:58,254 ERROR __main__: All official CTU-13 download URLs failed.
2026-10-16 13:14:58,254 ERROR __main__: Task T002 failed: CTU‑13 download failed and no fallback is permitted for Task T002.

## Platform-owned paths written inside the project

A script in this project created `state/` inside the project directory. Those names belong to the platform, and a copy of them here is a SHADOW: the verifier resolves the paths a task names relative to this project, so it reads the shadow instead of canonical state and rejects work on the strength of a stale record.

Write your outputs under `data/`, `figures/`, `code/` and `paper/`. Do not record artifact hashes, run state or project status yourself — the platform owns `state/` and derives hashes at verification time. Delete the directories listed above and drop whatever step created them.
