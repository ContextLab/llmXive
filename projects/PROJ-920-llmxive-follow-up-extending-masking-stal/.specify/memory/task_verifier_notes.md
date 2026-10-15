# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — Checked `code/validate_trajectories.py` and `tests/unit/test_trajectory_schema.py`. The validator uses a relaxed tolerance of 0.07 bits/token instead of the required ±0.01 bits/token and treats the `is_last_turn` flag as optional, violating the specification. The unit test references `contracts/trajectory.schema.yaml`, which is not present in the provided artifacts, so the test cannot pass. Additionally, the script’s success condition expects “All 500 trajectories…”, but the supplied JSON file’s length cannot be confirmed as 500. These issues mean the task’s requirements are not genuinely met.
- **T014** — Checked `code/simulate_agent.py`, `data/raw/trajectories.json`, `code/config/simulation_config.json`, `data/logs/simulation_results.csv`, and `contracts/simulation_log.schema.yaml`. The script loads the entire trajectory JSON into memory (no true streaming) and sets a memory limit of 7 GB, not the required ≤ 2 GB, and does not correctly handle the “last‑turn” edge case. Hence the implementation does not meet the task’s RAM‑budget and edge‑case requirements.
- **T015** — Requested task execution failed; rerun successfully: code/validate_simulation.py exit=-1 (TIMEOUT)
- **T016** — Requested task execution failed; rerun successfully: code/analyze_results.py exit=1
- **T027** — Requested task execution failed; rerun successfully: code/validate_regime_map.py exit=1
