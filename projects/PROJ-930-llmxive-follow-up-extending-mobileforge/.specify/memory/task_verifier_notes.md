# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T002** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T003** — The provided artifacts pertain only to the MobileForge logic‑distillation specification and contain no configuration files, scripts, or documentation for setting up ruff linting or black formatting. No `pyproject.toml`, `ruff.toml`, `black.toml`, or related setup instructions are present, so the linting/formatting tools have not been configured as required.
- **T004** — No `state/` directory or any checksum/versioning files are present in the provided artifacts; without tangible evidence of the directory’s creation and its contents, the requirement cannot be confirmed as satisfied.
- **T005** — No `utils/emulator.py` file or its contents were provided; consequently the required functions (`launch_emulator()`, `send_action(action_seq)`, `check_crash()`, `get_screenshot()`) and error codes (`EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`) are absent. The task cannot be considered completed until this module is present and implements the specified interface.
- **T005a** — declared artifact(s) missing/empty/invalid: tests/unit/test_emulator.py
- **T006** — No `utils/metrics.py` file or any code defining base classes for “Success Rate” and “Step Efficiency” was provided; thus the required artifact is missing. The task cannot be considered completed until the file exists with appropriate class implementations.
