# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory hierarchy (`src`, `tests`, `data`, `results`, `data/raw`, `data/processed`, `state`) was presented; without visible artifacts we cannot confirm the `mkdir -p` command was executed. The implementer must provide a listing or screenshots showing the created project structure.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff` section, or a pre‑commit hook file) were presented, so there is no evidence that ruff and black have been set up for the project. The required artifacts are missing.
- **T006** — declared artifact(s) missing/empty/invalid: src/data_models.py
- **T005** — declared artifact(s) missing/empty/invalid: src/loader.py
- **T007** — declared artifact(s) missing/empty/invalid: src/utils.py
- **T009** — declared artifact(s) missing/empty/invalid: src/validators.py
- **T010** — The repository lacks the required `src/topology.py` implementation, so the tests cannot import `compute_metrics`. Moreover, the existing `tests/test_topology.py` does not contain the specified Barabási‑Albert graph test (degree sum vs. 2·edges, clustering ≥ 0, path length check). Both the implementation file and the correct test case are missing.
- **T011** — The repository lacks `src/simulation.py`, so the imported functions cannot be tested, and `tests/test_simulation.py` does not contain the required RK45 integration/threshold‑detection test on a 200‑node ring graph with a 5 % analytical tolerance. The task’s core requirement is therefore unmet.
- **T013** — declared artifact(s) missing/empty/invalid: src/topology.py
- **T014** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T015** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T016** — declared artifact(s) missing/empty/invalid: results/sim_results.json
- **T017b** — declared artifact(s) missing/empty/invalid: src/simulation.py, results/verification_report.json
- **T020b** — The repository lacks the required `src/stats.py` file (it is missing), and there is no unit test present that checks the VIF‑>5 ridge fallback behavior or logs the alpha parameter. Both the implementation and its test are absent, so the task is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: src/stats.py
- **T021b** — The repository lacks the required `src/stats.py` module (file is missing) and there is no unit test file present that checks the default exclusion of non‑authorized features. Without these artifacts, the task cannot be considered fulfilled.
- **T022** — The required output files `results/sim_results.json` and `data/processed_metrics.csv` are both missing, and no evidence of updated `main.py` logic is provided. Without these artifacts, the aggregation and regression trigger cannot be verified.
- **T023a** — declared artifact(s) missing/empty/invalid: src/stats.py
- **T023b** — declared artifact(s) missing/empty/invalid: src/stats.py
