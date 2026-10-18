# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/verify_setup.py exit=1
- **T014** — `code/runtime.py` is a reasonable instrumentation module and `data/processed/runtime_report.json` exists with all ten stages and `total_seconds` ≤ 21600, but the recorded durations (mostly ~2e-06 s, total 0.0023 s) are physically impossible for a real pipeline run — they indicate the report was produced by a trivial script that started/ended stages with no work between them, i.e., fabricated timing data rather than measurements from an actual full pipeline run. Additionally, there is no evidence the instrumentation is integrated at the pipeline entry point (no modified `code/main.py` or simila
- **T002** — Requested task execution failed; rerun successfully: code/data_acquisition.py exit=1
