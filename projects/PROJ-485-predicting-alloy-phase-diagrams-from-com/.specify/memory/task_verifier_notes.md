# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T030** — The `resource_monitor.py` file is truncated (e.g., the `monitor_loop` lacks a proper `time.sleep` call and the wrapper’s final logic isn’t shown), and the required `data/artifacts/resource_log.json` file does not exist, so the logging and enforcement requirements are not demonstrably fulfilled.
- **T055** — The required `data/artifacts/fidelity_report.json` file does not exist, and the provided `plot_phase_diagrams.py` is truncated and lacks any implementation that writes such a report. Consequently the task’s core output and verification step are missing.
- **T059** — The repository lacks the required `data/logs/pipeline.log`, any `<system_id>_placeholder.png` plot, and a completed `fidelity_report.json`. Moreover, `code/viz/plot_phase_diagrams.py` is truncated and does not contain logic to detect missing ground‑truth, generate a red “NO DATA” overlay, or log `MISSING_GROUND_TRUTH`. Consequently the visualization fallback behavior is not implemented.
