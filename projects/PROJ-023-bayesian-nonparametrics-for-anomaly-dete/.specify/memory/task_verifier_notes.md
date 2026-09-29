# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T028** — The required image `paper/figures/fig1_timeseries.png` is absent, and the provided `render_fig1.py` script (truncated) does not show a `plt.savefig` call to actually write the figure to that path. The task’s core deliverable – the saved figure – is therefore missing.
- **T029** — The provided `render_fig2.py` is truncated and contains placeholder logic (e.g., random correlation matrix, unfinished `plt.save` call) and does not actually write the required PNG. Moreover, the expected output file `paper/figures/fig2_method_comparison.png` is missing. The task’s deliverables are therefore not satisfied.
- **T030** — No `paper/results.md` file was provided; the required summary document is missing, so the task’s artifact has not been delivered.
- **T032** — No artifact (report, script output, diff, or documentation) was provided showing that file paths in the code were checked against the `tasks.md` specifications, nor any evidence that mismatches (e.g., `scripts/` vs `code/scripts/`) were identified and corrected. The required verification evidence is missing.
- **T061** — declared artifact(s) missing/empty/invalid: ruff.toml
