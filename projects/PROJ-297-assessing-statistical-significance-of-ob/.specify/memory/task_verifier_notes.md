# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T041** — The `code/main.py` only defines a `timer` context manager but never uses it to wrap the full pipeline, nor does it write any JSON file to `output/reports/runtime_log.json` (the file is missing). Consequently the runtime is not measured, logged, or validated against the time limit as required.
- **T060** — The provided `code/main.py` only defines a `timer` context manager but never uses it around the pipeline stages, nor does it write any timing results to `output/reports/profiling_log.json`. The expected JSON log file is absent from the repository. Consequently, the profiling step and required output are not implemented.
