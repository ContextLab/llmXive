# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or file manifests were supplied, so there is no evidence that the required folders (`src/`, `src/environment/`, `src/agent/`, `src/simulation/`, `src/analysis/`, `tests/`, `data/raw/synthetic_graphs/`, `data/processed/`) actually exist in the project. The implementer must provide a concrete view (e.g., a tree dump or screenshots) showing these directories are present and non‑empty.
- **T004** — declared artifact(s) missing/empty/invalid: src/config.py
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/metrics.py
- **T006** — declared artifact(s) missing/empty/invalid: src/simulation/runner.py
- **T007** — declared artifact(s) missing/empty/invalid: src/environment/state_graph.py
- **T008** — declared artifact(s) missing/empty/invalid: src/config.py
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/metrics.py
- **T010** — declared artifact(s) missing/empty/invalid: src/environment/graph_generator.py
- **T011** — No code or other artifact defining a `generate_tier_1` method is present; the repository contains no implementation that creates a single deterministic path, enforces the node‑count range, checks `graph.is_valid()`, or loops to regenerate invalid graphs. The required method is therefore missing.
- **T017** — declared artifact(s) missing/empty/invalid: src/agent/opid_router.py
- **T020** — No code, configuration, or test artifacts were provided to demonstrate that the OPID agent now suppresses hindsight skill injection when the routing threshold is set to 1.0 (or any value that should block injection). Without any files, functions, or logs showing this behavior, the requirement is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: src/simulation/runner.py
- **T022** — declared artifact(s) missing/empty/invalid: src/simulation/runner.py
- **T023** — No code, script, or data implementing a threshold sweep from 0.0 to 1.0 in 0.1 increments was provided; the evidence section contains no artifacts to inspect, so the required sweep logic cannot be verified. The implementer must supply the actual implementation (e.g., a function, loop, or experiment runner) and any resulting logs or outputs demonstrating the iteration over the specified thresholds.
