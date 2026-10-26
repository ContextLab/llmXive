# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quickstart guide’s “sample” command runs only a hard‑coded smoke test, not a real 5‑sample subset downloaded via the data‑extraction script, and the required log file `logs/quickstart_run.log` is not present among the artifacts. Consequently the test does not fully meet the task’s specifications.
- **T003** — Requested task execution failed; rerun successfully: code/data_extraction.py exit=1
- **T004** — The repository lacks the required UI files (`annotation_ui/index.html`, etc.) and the gold‑standard CSVs (`data/gold/sample_for_annotation.csv`, `annotator_1.csv`, `annotator_2.csv`). `gold_annotation.py` writes its JSON to a different path, never reads the annotator CSVs, does not abort when κ < 0.6, and does not produce a `conflicts.log`. These missing/incorrect artifacts mean the task’s specifications are not met.
- **T005** — The markdown file lacks the required “CPU‑only compatibility” column and its scale‑limitation sentence does not contain “comparable” or “similar”, causing `test_scale_limitation_sentence` to fail (see test log). Consequently the verification test does not pass and the task is not fully satisfied.
