# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — The provided `code/03_compute_graph_metrics.py` file is present and mentions `joblib.Parallel(n_jobs=2)`, but the excerpt is truncated before any actual Parallel call or a main processing loop, so we cannot confirm that the script truly runs subjects in parallel. Moreover, there is no evidence (e.g., timing logs, benchmark report) showing that the runtime for 100 subjects is under 30 minutes. The implementer must include the full script demonstrating Parallel usage and provide measured runtime results to satisfy the task.
