# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — No code, test, or documentation for a `generate_tier_2` method is present; the required implementation that creates a 20‑50 node stochastic graph with internal retry logic (max_retries=100) and validates via `graph.is_valid()` is missing. The evidence does not contain any artifact that could be inspected to confirm the method exists or meets the specifications.
- **T013** — No code, test, or documentation for a `generate_tier_3` method is present; the repository provides no implementation, graph‑generation logic, retry loop, or validation checks required by the task. Consequently the required artifact is missing.
- **T015** — No code, test, or script implementing the `verify_deterministic_regeneration` task is present; there is no artifact that runs the generator with a fixed seed, computes checksums, regenerates, recomputes, and asserts equality. Consequently the required functionality is missing.
- **T018** — No code artifact showing the `OPIDRouter.should_inject` method was provided, nor any evidence (e.g., unit tests, documentation, or commit diff) that the Bernoulli‑trial logic with probability = 1 − threshold has been added. The required implementation is missing.
- **T019** — declared artifact(s) missing/empty/invalid: src/agent/opid_router.py
- **T022** — declared artifact(s) missing/empty/invalid: src/simulation/runner.py
- **T023b** — declared artifact(s) missing/empty/invalid: data/processed/validation_set_config.json
- **T024** — The submission provides only the high‑level user stories and specifications; there is no code, script, log file, or dataset demonstrating an episode loop that actually runs exactly 1,000 simulated episodes for each (Tier, Threshold) pair. Consequently, the required artifact (the implemented loop and its execution evidence) is missing.
- **T025** — declared artifact(s) missing/empty/invalid: src/simulation/runner.py
- **T026** — No code, function, script, or data file implementing the “success rate” metric is present; the provided description contains only high‑level user stories and no concrete artifact that computes or records the percentage of episodes that follow the ground‑truth path. Consequently the required implementation is missing.
- **T027b** — declared artifact(s) missing/empty/invalid: src/analysis/stats.py, data/processed/entropy_regression.json
