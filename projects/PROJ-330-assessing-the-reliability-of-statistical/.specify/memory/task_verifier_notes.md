# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The evidence includes a `requirements.txt` containing the required Python packages (plus an extra `scipy`), but there is no artifact showing an R 4.3 environment (e.g., Dockerfile, renv lockfile, or similar). The task’s R‑environment requirement is unmet.
- **T003** — The log shows that `setup_lint_tools.sh` installed flake8 and ran it on the code, but there is no evidence that Black was installed, configured, or invoked (no black version output, no formatting run, and no Black configuration file such as `pyproject.toml` or `black.toml`). To satisfy the task, add artifacts confirming Black’s installation and configuration (e.g., a `pyproject.toml` with Black settings and a log showing `black --check` or a formatting run).
