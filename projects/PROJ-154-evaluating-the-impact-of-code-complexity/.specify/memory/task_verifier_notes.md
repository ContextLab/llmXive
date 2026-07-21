# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (`code/`, `data/`, `results/`, `tests/`) is present; the provided description contains only specifications and no actual file system artifacts. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- **T003** — The submission provides no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or scripts that set up ruff and black. Consequently, the required artifact for task T003 is missing.
- **T004** — declared artifact(s) missing/empty/invalid: config.yaml
- **T004#1** — The `code/utils/memory_guard.py` file is present but its content is truncated (e.g., an unfinished `logging.error` line and missing function closure), so the implementation is incomplete. Additionally, the required `config.yaml` file defining the memory threshold does not exist. Both the missing configuration and the incomplete Python module prevent the task from being fully satisfied.
- **T007** — No code, configuration file, or documentation was provided that sets a deterministic random seed, configures logging, or records the `radon` library version as required by task T007. The implementer must supply the actual implementation (e.g., a Python module or config script) that performs these actions.
- **T010** — The required file `tests/unit/test_complexity_calc.py` does not exist, so no unit test for the radon metric calculation is present. The task’s primary artifact is missing, making the claim unsubstantiated.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/exclusions.log
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/annotated_metrics.csv
- **T016** — No CSV file, verification script, log, or report was provided to demonstrate that every row contains valid numeric values for the three metrics; thus the required evidence of verification is missing.
- **T018** — declared artifact(s) missing/empty/invalid: code/02_bug_injection.py, data/processed/bug_injected.csv
- **T018#1** — declared artifact(s) missing/empty/invalid: code/02_truncation.py, data/processed/truncated_code.csv
