# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided evidence only contains a feature specification excerpt; there is no visible `code/`, `data/`, `tests/`, or `specs/` directory (or any files within them) to confirm that the required project structure was created. The implementer must add the requested top‑level folders with appropriate content to satisfy task T001.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or related scripts) were presented in the `code/` directory, so the required artifact does not exist or is empty. The task therefore remains unfinished.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T020** — The provided `stats.py` does not contain any function that loops over the cutoffs [2, 3, 4], computes `spike_point`/`slope_change`, and writes them to `data/results/sensitivity_analysis.json`. Moreover, the required JSON output file is absent from the repository. Consequently the task’s core requirements are not met.
- **T021** — The repository lacks the required output files (`data/processed/execution_logs.csv` and `data/results/anova_results.json`), and the provided `code/main.py` excerpt does not show any logic that writes raw metrics to the CSV or aggregated stats to the JSON. Consequently, the claimed data‑persistence feature is not actually implemented.
