# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042** — The provided `timeout_guard.py` defines a `_log_timeout_trace` function but the implementation is truncated and never shows the actual file‑write operation; consequently the required `results/timeout_traces.log` does not exist. The task is not satisfied until the function writes a JSON line containing the agent name, task ID, and step to that log file.
- **T043** — The provided `power_calculator.py` stops short of generating or updating `results/statistical_report.json` and does not contain any code that adds a `power_warning` field when power < 0.4. Moreover, the required `results/statistical_report.json` file is absent entirely. The task’s core requirement—writing the warning into the report—is therefore unmet.
