# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided evidence shows the `code` and `tests` directories with the required files, but there is no proof that the `data`, `state`, and `docs` directories were created (they are not listed or contain any files). These missing directories mean the full project structure task is not satisfied.
- **T002** — The provided `requirements.txt` lists numpy, scipy, matplotlib, pytest, black, and flake8, but it does **not** contain the required `sympy` package. Consequently the file does not meet the task specification.
- **T003** — The repository contains a correct `pyproject.toml` with the required Black and pytest sections, but there is no `.flake8` file (or its contents) present to satisfy the linting configuration requirement. The missing `.flake8` file must be added with the specified `[flake8] max-line-length = 100` content.
- **T004** — The provided `code/dickman.py` does not use `scipy.integrate.odeint` at all, nor does it set the required tolerances (`rtol=1e-6`, `atol=1e-9`). Instead it implements a custom trapezoidal integration with NumPy, which fails the core specification. The task therefore remains unfinished.
- **T023a** — declared artifact(s) missing/empty/invalid: data/density_measurements_spec.csv
- **T023b** — declared artifact(s) missing/empty/invalid: data/density_measurements_plan.csv
- **T023c** — declared artifact(s) missing/empty/invalid: data/density_measurements_sensitivity.csv
- **T023d** — declared artifact(s) missing/empty/invalid: data/density_measurements_spec.csv, data/density_measurements_plan.csv
- **T026a** — Requested task execution failed; rerun successfully: code/run_plan_analysis.py exit=1
