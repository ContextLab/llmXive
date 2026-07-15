# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T026** — The provided `statistical_analysis.py` defines `compute_power_cohen_d` and a `PowerAnalysisResult` dataclass, but it never checks the computed power against the 0.8 threshold nor logs a warning when the threshold is not met. No function ties the effect‑size, sample‑size, and threshold enforcement together, so the required “enforce ≥ 0.8 power and log warnings otherwise” behavior is missing.
