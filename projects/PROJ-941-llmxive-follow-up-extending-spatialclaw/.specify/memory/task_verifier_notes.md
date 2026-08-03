# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (code/, data/, results/, tests/) is provided; the implementer did not supply a directory listing or any files showing that the structure has been created.
- **T003** — The implementer supplied only a feature specification for a spatial‑reasoning experiment and no files or configuration related to linting/formatting. There is no `pyproject.toml`, `.ruff.toml`, `black` config, or any documentation showing ruff and black have been set up, so the required artifact is missing.
- **T006** — The required output file `data/raw/synthetic_spatialclaw_v1.json` does not exist, so the generator script has not produced the dataset as specified. Consequently the task’s primary deliverable is missing.
- **T010** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T011** — No logging infrastructure code, configuration, or sample execution logs were provided. The claim lacks any artifact demonstrating that seed values and blocked operation details are captured, so the requirement is not satisfied.
- **T035b** — The `code/stats/power_analysis.py` file is truncated (e.g., an unfinished line in `validate_budget`) and contains no logic to write `data/power_analysis_report.json`. Moreover, the required JSON report file is missing from the repository.
- **T036** — No code, logs, or report artifacts were supplied to demonstrate that a 2‑D‑only execution kernel was implemented, that imports of 3‑D libraries are blocked, that stochasticity control is enforced, or that performance metrics and a paired 2D/3D comparison report were generated. The required deliverables are missing.
- **T023b** — The required output file `data/baseline_spatialclaw.csv` does not exist, indicating the baseline agent was not executed and the paired dataset was not generated as specified. The implementer must run `baseline_3d.py` on the exact task instances and produce the CSV file in the `data/` directory.
- **T025** — declared artifact(s) missing/empty/invalid: results/analysis/paired_comparison.csv
- **T026** — No code, configuration, test results, or documentation were provided that demonstrate the implementation of logic to subtract blocked 3D library initialization time from step latency calculations. The required artifact (e.g., modified latency‑calculation module, unit tests, or logs showing the exclusion) is missing.
