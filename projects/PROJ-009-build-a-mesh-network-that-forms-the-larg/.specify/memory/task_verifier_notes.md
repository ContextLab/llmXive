# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The response contains only the task description and no evidence of the required directory tree, `__init__.py` files, or a `.gitignore`. Without the actual project structure present on disk, the claim that the task is complete cannot be verified. The missing artifact is the full folder hierarchy (`code/orchestrator`, `code/analysis`, etc.) with the required files.
- **T013c** — No `heartbeat_monitoring.py` file (or any code) was provided in the evidence, so there is no implementation to verify for heartbeat loss detection or task re‑assignment logic. The required artifact is missing.
- **T012** — No `remote_tools_manager.py` file (or its contents) was presented in the evidence, so we cannot confirm that the required module exists, is non‑empty, or implements the verification and installation of CLI tools on remote nodes. The implementer must provide the actual source file with the expected functionality.
