# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files or directory listing were provided, so we cannot verify that a `projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim/` structure matching `plan.md` actually exists. The required artifact is missing.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `pyproject.toml` with Black settings, or corresponding CI scripts) were provided, nor any evidence that ruff and black have been set up in the `code/` directory. The required artifacts are missing.
- **T050** — The repository contains an `update_state_file` helper that hashes files and writes a YAML, but the CLI does not invoke it for a `--update-state` command, it does not recursively walk `data/processed/`, and the expected state file `state/projects/PROJ-938-llmxive-follow-up-extending-trisplat-sim.yaml` is absent. The task’s core artifact (the updated state YAML) is missing, so the requirement is not met.
