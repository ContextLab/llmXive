# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — Requested task execution failed; rerun successfully: code/sensitivity.py exit=-1 (TIMEOUT)
- **T014** — The only artifact provided is `code/viz.py`; the required PNG files `outputs/figures/heatmap_L{L}.png` are missing, and the script’s zero‑line (`plt.axhline(y=-0.5)`) does not correctly draw a horizontal line at autocorrelation = 0, nor does the confidence‑band overlay align with the heat‑map axes. The task’s visual output is therefore not satisfied.
- **T016** — The `research.md` file is present and contains methods, results, and a discussion of the theoretical variance, but it does not list the exact row numbers (or figure indices) that support each claim, nor does it enumerate the specific interval start indices flagged by `sensitivity_flag`. The claim‑to‑artifact links are given only as conditions (e.g., “rows where `adjusted_p_value ≥ 0.05`”) rather than concrete row identifiers, which fails the task’s requirement for precise linking.
- **T017** — Requested task execution failed; rerun successfully: code/main.py exit=1
