# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `pyproject.toml` correctly defines `[tool.black]` with `line-length = 88` and `[tool.ruff]` with `select = ['E', 'F', 'W']`, but a separate `.ruff.toml` file is still present, contradicting the requirement that the single `pyproject.toml` replace any standalone Ruff (or Black) configuration files. The extra `.ruff.toml` must be removed for the task to be considered complete.
- **T006b** — The `RegressionResult` class is present, but the fields `fdr_corrected_p_logic` and `fdr_corrected_p_fidelity` are defined as mandatory `float` types, not `Optional[float]` as the task specifies. This prevents instantiation without those values, violating the requirement. The model must be updated to make those two fields optional.
- **T029** — declared artifact(s) missing/empty/invalid: outputs/regression_report.md, outputs/correlation_diff_test.json
- **T032** — declared artifact(s) missing/empty/invalid: outputs/memory_profile.log
- **T042** — Requested task execution failed; rerun successfully: code/scripts/generate_methodology_report.py exit=-1
