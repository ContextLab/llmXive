# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or similar) are present in the provided evidence, nor any scripts or documentation showing that ruff and black have been set up for the project. The claim therefore does not satisfy the requirement to configure these tools.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — The `data_loader.py` contains a stub of validation logic and attempts to load `contracts/dataset.schema.yaml`, but the required schema file is missing from the repository, so the function cannot actually enforce schema compliance. Additionally, the provided code is truncated and does not show a complete implementation of zero‑relevance query warnings. The task therefore remains unfinished.
- **T027** — declared artifact(s) missing/empty/invalid: results/analysis_framing.txt
- **T029** — The provided `visualization.py` contains only data‑loading utilities and does not include any code that creates density plots or reads `results/analysis_framing.txt` (which is also missing). There is no fallback string handling for a missing framing file, nor any plot‑title/caption logic, so the core requirement of generating the comparative density visualizations with the framing text is not satisfied.
