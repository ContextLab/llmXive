# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — The provided `tracing.py` stops after defining helper functions and does not contain the main logic to load SiT‑XL/2, iterate over the validation set with the specified fixed timestep schedule, enforce `memory_guard(7.0)`, save per‑image `.npy` files with the required 4‑D shape, or write the required JSON‑lines logs. Additionally, the expected log files `data/results/tracing_log.jsonl` and `data/results/memory_profile_raw.jsonl` are absent. The script therefore does not meet the task specifications.
- **T031c** — No artifact (e.g., a grep result, code diff, or updated source files) was provided to demonstrate that all `print(` calls in `src/` have been removed and replaced with logging. Without such evidence, the claim cannot be verified.
