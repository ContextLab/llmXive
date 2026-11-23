# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required sub‑directories `results/plots/` and `results/reports/` are missing, and the provided code listing does not include any visible validation logic that checks the directory structure’s existence and writability before execution.
- **T003** — Checked `code/pyproject.toml` – it contains the required `[tool.black]` section with `line-length = 88`. The required `code/.flake8` file is missing entirely, so the task’s full linting/formatting configuration is not provided. Adding a `.flake8` file with the specified `[flake8]` settings will be needed.
- **T004a** — Checked `projects/PROJ-504-evaluating-the-impact-of-variable-select/code/config.py`; the file exists but does not define a `pilot_simulations_per_condition` attribute (or default value of 10) as required by task T004a. The default configuration lacks this setting, so the task is not fulfilled. Adding `pilot_simulations_per_condition: int = 10` (or similar) to the Config dataclass or module-level default would resolve the issue.
- **T045** — `code/utils/watchdog.py` is missing entirely, and the existing `code/analysis/selectors.py` only contains LASSO‑based selection code; it does not implement stepwise selection with early‑stopping based on an AIC improvement threshold of 0.01 nor predictor‑pruning based on a 0.95 correlation threshold. Both required optimizations are absent.
- **T046** — The provided `code/analysis/selectors.py` only implements LASSO selection; it contains no forward stepwise selection routine, no AIC‑based early‑stopping condition (improvement > 0.01 for N steps), and no preprocessing step that removes predictors with pairwise correlation > 0.95. Consequently the required early‑stopping and predictor‑pruning logic is absent.
- **T052** — declared artifact(s) missing/empty/invalid: code/data/validator.py
- **T057** — declared artifact(s) missing/empty/invalid: code/utils/watchdog.py
- **T055** — declared artifact(s) missing/empty/invalid: code/analysis/comparators.py
- **T038** — declared artifact(s) missing/empty/invalid: code/analysis/comparators.py
- **T039** — declared artifact(s) missing/empty/invalid: code/analysis/comparators.py
- **T039b** — declared artifact(s) missing/empty/invalid: code/analysis/comparators.py, results/reports/holm_pvalues.csv
- **T040** — declared artifact(s) missing/empty/invalid: code/viz/plots.py, results/plots/
- **T041** — declared artifact(s) missing/empty/invalid: code/viz/plots.py, results/plots/
- **T056** — declared artifact(s) missing/empty/invalid: code/analysis/comparators.py, results/reports/sensitivity_report.csv
- **T067** — declared artifact(s) missing/empty/invalid: code/verify_repro.py, state/checksums.json
