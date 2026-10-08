# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The provided `preprocess.py` defines helper functions (`load_schema`, `validate_schema`) but the file is truncated before the implementation of `validate_schema` and there is no code shown that calls `jsonschema.validate` on the filtered DataFrame. Consequently, we cannot confirm that the schema is loaded and validation is performed after filtering, as required. The task needs a concrete call to `jsonschema.validate` (or equivalent) on the filtered data.
- **T026** — The `code/data/compute_metrics.py` shown does not contain any code that logs a “CONVERGENCE: X% success, Y failed fits” message nor writes aggregated statistics to `results/convergence_stats.json`. Moreover, the required `results/convergence_stats.json` file is absent from the repository. The task’s core output is therefore missing.
- **T038** — declared artifact(s) missing/empty/invalid: results/statistics.json
- **T039** — No PNG or PDF files are present in a `results/figures/` directory, nor is there any code or script shown that writes visualizations to that location. The required artifact (saved visualizations) is missing, so the task is not satisfied.
- **T043** — The repository lacks the required `code/main.py` script and the generated `results/timing.json` file, so the pipeline cannot be timed or validated as specified. These essential artifacts must be added and the timing assertion verified.
