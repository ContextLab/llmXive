# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The provided tree only contains top‑level `__init__.py` files; none of the newly created sub‑directories under `code/` (e.g., `analysis/`, `cache/`, `data/`, `pipeline/`, `reproducibility/`) or under `tests/` (`integration/`, `unit/`) have an `__init__.py`. Empty `__init__.py` files must be added to each of those directories to satisfy the task.
- **T002** — The provided `requirements.txt` exists but lists the packages without version pins and includes an extra `pytest-benchmark` entry not requested. The task explicitly required a pinned `requirements.txt` for the specified seven packages.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff.toml` section, or a pre‑commit hook file) were provided, nor any evidence that `ruff` and `black` have been installed or run. Without these artifacts the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T004** — No pytest configuration files (e.g., `pytest.ini` or `conftest.py`) or any evidence of the `pytest-benchmark` plugin being added to the test environment are present, so the required setup is missing.
- **T024** — declared artifact(s) missing/empty/invalid: code/analysis/metrics.py
- **T025** — declared artifact(s) missing/empty/invalid: code/analysis/stats.py, data/derived/statistics.json
- **T030** — declared artifact(s) missing/empty/invalid: data/derived/results.csv
- **T031** — declared artifact(s) missing/empty/invalid: data/derived/statistics.json
- **T033** — declared artifact(s) missing/empty/invalid: code/analysis/visualization.py
- **T034** — declared artifact(s) missing/empty/invalid: code/main.py
- **T035** — declared artifact(s) missing/empty/invalid: data/derived/sensitivity_analysis.csv
- **T037** — declared artifact(s) missing/empty/invalid: data/derived/trade_off_curve.png
- **T041** — Requested task execution failed; rerun successfully: code/verify_final.py exit=1
