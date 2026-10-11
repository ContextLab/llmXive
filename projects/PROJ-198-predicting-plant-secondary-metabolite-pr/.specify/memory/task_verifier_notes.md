# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The required `.flake8` file is missing entirely, and the historical execution log shows the verification actually failed: ruff could not parse a `.ruff.toml` (TOML parse error on `line-length`) and `black --check` reported dozens of files "would reformat", so neither `ruff --quiet .` nor `black --check .` exited 0. The implementer must add `.flake8`, fix the ruff config (the current `.ruff.toml` has no `line-length` issue but the run log shows a conflicting `code/.ruff.toml`), and re-run until both checks pass with exit code 0.
- **T003** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=2
- **T005** — Requested task execution failed; rerun successfully: code/scripts/run_lint_check.py exit=2
