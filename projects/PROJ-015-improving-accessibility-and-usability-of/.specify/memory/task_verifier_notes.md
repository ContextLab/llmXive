# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019d** — No code artifacts (e.g., modified `app.py` showing a call to `validate_session` before writing to `data/raw/`, or updated `validator.py` integration) were provided. Without visible changes or evidence that a `ValueError` is raised on validation failure, the task requirement is not demonstrably satisfied.
- **T023a** — The repository contains a partially‑implemented `run_anova_rm` function (the file is truncated and does not show writing the required `metrics_summary.csv`). Moreover, the expected output file `data/processed/metrics_summary.csv` is missing entirely, so the task’s output artifact is not present. The implementation must be completed and the CSV generated to satisfy the requirement.
- **T027a** — The `visualizer.py` contains the plotting function, but the required output file `figures/completion_time.png` does not exist (no file on disk), so the verification conditions (existence, non‑zero size, PNG header) are not met. The implementer must generate and commit the PNG file.
- **T027b** — declared artifact(s) missing/empty/invalid: figures/error_count.png
- **T027c** — declared artifact(s) missing/empty/invalid: figures/sus_score.png
- **T123** — No `power_report.md` file or its contents were provided, so we cannot confirm that it contains the required strings “N=30” and “statistical power”. The implementer must supply the generated `power_report.md` showing the explicit sample‑size check and explanation.
