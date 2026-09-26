# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T002** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `pyproject.toml` with Black settings, or CI scripts invoking ruff/black) are present in the provided evidence, so the required artifact to claim the task completed is missing.
- **T004** — No `state/` directory or any checksum/versioning files were presented; the implementer provided only the feature specification for logic distillation, which does not address the required setup of a `state/` directory for artifact checksums and versioning. The required artifact is missing.
- **T005** — No `utils/emulator.py` file or any code defining the required functions (`launch_emulator`, `send_action`, `check_crash`, `get_screenshot`) and error codes (`EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`) is present in the provided artifacts. The task therefore remains unimplemented.
- **T006** — No `utils/metrics.py` file or any code defining base classes for “Success Rate” and “Step Efficiency” was provided. The required artifact is missing, so the task is not satisfied.
- **T008** — No configuration file, script, or documentation was provided to set up environment variables for dataset paths and random seeds, which is the core requirement of task T008. The artifacts shown relate only to dataset extraction, model training, and evaluation, not to environment variable management.
- **T009** — No `utils/power_analysis.py` file or `calculate_required_n` function was presented, and there is no `state/validated_n.json` output shown. Without these artifacts, the task requirements are not satisfied.
- **T019a** — No updated `spec.md` file is provided, nor any excerpt showing that FR-005 now reads “McNemar's test (for binary paired outcomes)” instead of “paired t-test”. Without the actual document change, the requirement cannot be confirmed as satisfied.
