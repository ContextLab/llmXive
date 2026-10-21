# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required `data/raw/nist_refs.json` file (and its `nist_refs.json.sha256` checksum) are missing, so the loader cannot load three validated entries and the unit tests that expect the file to exist will fail. Without the curated JSON and its checksum, the task’s core deliverable is not satisfied.
- **T002** — Requested task execution failed; rerun successfully: code/tests/test_simulation.py exit=2
- **T003** — The `code/tests/test_diffusion.py` imports `analysis.diffusion` and `analysis.msd`, but the project only contains `code/analysis/...` without an `analysis` package, so the tests cannot be imported. Moreover, the linear‑case test computes the expected diffusion coefficient in m² s⁻¹ yet the implementation’s `calculate_diffusion_coefficient` returns a value in m² ns⁻¹ (missing the 1 ns = 1e‑9 s conversion), causing the asserted `np.isclose(..., D_true)` check to fail. Consequently the required pytest suite does not pass.
- **T004** — Requested task execution failed; rerun successfully: code/pipeline.py exit=2
