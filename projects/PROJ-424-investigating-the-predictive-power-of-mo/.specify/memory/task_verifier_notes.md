# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Requested task execution failed; rerun successfully: code/tests/test_simulation.py exit=2
- **T003** — The provided `code/tests/test_diffusion.py` does not pass: the linear‑case test fails because the monkey‑patch replaces `analysis.msd.load_trajectory_timeseries`, while `diffusion.py` imports `msd` via a relative import (`from .msd import …`), leaving the original loader unchanged and causing a “Trajectory not found” error. Consequently the required `pytest code/tests/test_diffusion.py` does not succeed. The import structure must be aligned (or the test adjusted) so the synthetic data are used, and then all tests must pass.
- **T004** — Requested task execution failed; rerun successfully: code/pipeline.py exit=2
