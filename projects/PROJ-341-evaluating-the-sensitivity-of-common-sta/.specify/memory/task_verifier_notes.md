# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T032** — The required output file `data/simulation/real_data_power.json` is missing, so no bootstrapped power estimates or KS distance verification have been provided. The task’s core deliverable is absent.
- **T036** — The provided `code/main.py` only defines a memory‑limit constant and helper functions (`get_memory_usage_mb`, `check_memory_limit`, `force_gc`) but the truncated file does not show these being used to control memory during the simulation, nor any benchmarks proving the program stays under 7 GB. Without evidence that the main loop enforces the limit or that memory usage has been measured and confirmed, the task requirement is not satisfied.
