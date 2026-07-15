# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files, directories, or any structural artifacts were presented; the response contains only the specification text and no evidence of a created codebase or folder layout. The required project structure is missing.
- **T002** — No `requirements.txt` file or any project initialization evidence was provided; the claim that the Python 3.11 project with the specified dependencies exists cannot be verified. The required artifact is missing.
- **T003** — No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or related setup scripts are presented. Without these artifacts, the claim that linting and formatting tools are configured cannot be verified. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T004** — The provided `data/checksums.txt` exists but only contains placeholder comments and no actual checksum entries, so the logging mechanism is not functional. A real implementation should record SHA‑256 hashes of data files as they are added to the `data/` directory.
