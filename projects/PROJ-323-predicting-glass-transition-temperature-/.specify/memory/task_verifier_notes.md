# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/ingest.py exit=1
- **T003** — The only artifact provided is `outputs/logs/runtime.json`, which does contain a numeric `elapsed_seconds` field, but there is no evidence that the pipeline was actually wrapped in a timer nor any CI log or test showing the required assertion that `elapsed_seconds <= 21600`. The implementer must supply the code that measures the runtime (e.g., using `time.perf_counter`) and CI output confirming the runtime check passes.
- **T004** — The `outputs/logs/memory.json` file exists and contains a valid `peak_rss_mb` value well below the 7000 MB limit, but there is no evidence (e.g., script, code snippet, CI log) showing that the value was obtained using `psutil` as required by the task. Provide the implementation that records peak RSS with `psutil` and evidence of its execution.
- **T005** — Requested task execution failed; rerun successfully: code/ingest_tg.py exit=1
- **T006** — Requested task execution failed; rerun successfully: tests/test_ingest_check.py exit=1
