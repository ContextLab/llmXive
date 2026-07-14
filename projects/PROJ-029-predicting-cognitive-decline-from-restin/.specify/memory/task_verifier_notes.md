# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T030b** — The provided `code/07_sensitivity_analysis.py` contains only helper functions and a docstring describing Part 2, but the visible code does not include any logic that varies the MMSE/MOCA decline‑definition threshold, re‑trains the model for each ±1‑point change, or records the resulting false‑positive/false‑negative rates. Without that implementation (or evidence of it later in the file), the task requirement is not met.
- **T035** — The provided `code/03_compute_graph_metrics.py` processes subjects sequentially and contains no import or use of `joblib.Parallel(n_jobs=2)`. Moreover, there is no accompanying benchmark, log, or report demonstrating that the runtime for 100 subjects dropped below 30 minutes. The required refactor and verification are missing.
