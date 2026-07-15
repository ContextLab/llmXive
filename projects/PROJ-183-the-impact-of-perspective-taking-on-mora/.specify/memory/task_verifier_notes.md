# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042** — The provided `code/main.py` contains a logging setup that would write to `data/logs/resource_metrics.log`, but the log file is absent, and the truncated `main()` function does not show that final metrics are actually logged. To satisfy the task, the script must invoke the logging at the end of the pipeline run and a non‑empty `data/logs/resource_metrics.log` file with the recorded metrics must be present.
