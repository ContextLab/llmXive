# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006** — The required output `data/logs/interactions_clean.jsonl` is 0 bytes (sha256 of empty file), so the ≥7,500 schema-valid log lines requirement is not met — the historical run of `simulate_participants.py` exited 0 with empty stdout and no evidence any lines were written (possibly the logger's `llmxive_toolkit.paths.data` wrote elsewhere, or logs were cleared). The power-analysis script itself is fine (prints N=34 ≥ 30, exit 0), but the simulation driver's deliverable is missing; re-run it and verify the canonical log file actually contains ≥7,500 valid JSON lines.
- **T007** — Requested task execution failed; rerun successfully: src/analysis/validation_by_session.py exit=1
- **T008** — Requested task execution failed; rerun successfully: src/analysis/wilcoxon_analysis.py exit=2
- **T018** — Requested task execution failed; rerun successfully: code/src/analysis/mean_wilcoxon_analysis.py exit=2
