# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory `projects/PROJ-212-exploring-the-impact-of-network-structur/code/` or any files within it was provided; without a visible project structure the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook) are present in the provided artifacts, nor any documentation showing that Ruff and Black have been set up for the project. Without these concrete files, the task of configuring linting and formatting tools is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: src/data_models.py
- **T005** — declared artifact(s) missing/empty/invalid: src/loader.py, data/synthetic_fallback_N30.csv
- **T007** — declared artifact(s) missing/empty/invalid: src/utils.py
- **T009** — declared artifact(s) missing/empty/invalid: src/validators.py
- **T010** — The test file `tests/test_topology.py` is present and contains realistic assertions, but the required source module `src/topology.py` does not exist, so the tests cannot be imported or executed. The missing implementation file must be added (or the import path corrected) for the unit test to be functional.
- **T011** — The required source file `src/simulation.py` is missing, so the imported functions (`check_disconnected`, `kuramoto_derivative`, `run_kuramoto_simulation`) do not exist. Additionally, the provided `tests/test_simulation.py` is truncated and incomplete (e.g., an unfinished fixture definition), meaning the unit tests are not fully defined or runnable. Both the implementation and the complete test suite are absent.
- **T013** — declared artifact(s) missing/empty/invalid: src/topology.py
- **T014** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T015** — declared artifact(s) missing/empty/invalid: src/simulation.py
- **T016** — declared artifact(s) missing/empty/invalid: results/sim_results.json
- **T017b** — declared artifact(s) missing/empty/invalid: src/simulation.py, results/verification_report.json
- **T018** — The required `src/stats.py` file does not exist, so there is no code to test, and consequently no unit test for VIF calculation or Ridge fallback logic can be present or validated. The missing source file must be added (with the VIF and Ridge logic) and a corresponding unit test created to satisfy the task.
- **T019** — declared artifact(s) missing/empty/invalid: src/stats.py
- **T020a** — declared artifact(s) missing/empty/invalid: src/stats.py
