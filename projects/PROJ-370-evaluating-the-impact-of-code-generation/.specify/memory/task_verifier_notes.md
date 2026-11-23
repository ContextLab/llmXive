# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the full `code/` hierarchy (src, tests, data, logs) is present, but the required `specs/001-eval-llm-review-quality/contracts` directory is not found in the listed artifacts. Adding that missing `specs/.../contracts` folder (and any needed contents) is needed to satisfy the task.
- **T003** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T005** — The CLI script exists and exits 0, producing a schema‑valid `data/results/smoke_report.json`, but there is no provided evidence that `logs/pipeline.jsonl` was created and contains the required `"cli_start"` event (the file’s content is not shown). Without confirming this log entry, the task’s verification criteria are not fully satisfied.
- **T007** — Requested task execution failed; rerun successfully: code/src/extraction/fetch_prs.py exit=-1 (TIMEOUT)
