# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T042** — The provided `timeout_guard.py` defines a `_log_timeout_trace` stub that is truncated and does not show any code that actually writes the agent name, task ID, and step to `results/timeout_traces.log`. Moreover, the expected log file does not exist, indicating the logging functionality is not operational. The implementation must include a complete function that writes a JSON line with the required fields to the log file.
- **T043** — The `results/statistical_report.json` file is absent, so the required warning cannot be recorded. Moreover, the provided `power_calculator.py` is truncated and shows no logic that fixes N = 10, computes power, or writes a `power_warning` field when power < 0.4. The task’s core output is therefore missing.
