# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T035** — The script exists and defines `JOBLIB_N_JOBS = 2`, but the provided excerpt is truncated before any call to `Parallel` and contains no code that actually runs the computation in parallel. Moreover, there is no evidence (e.g., timing logs, benchmark report) showing that the runtime for 100 subjects was measured and reduced to under 30 minutes. The required refactoring and verification are therefore not demonstrated.
