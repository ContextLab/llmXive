# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence was provided that a `code/` directory exists in the repository (e.g., a directory listing or any files inside it). Without such artifact, the requirement “Create `code/` root directory” cannot be confirmed.
- **T001d** — No checksum file was presented in `state/projects/...yaml`, nor any evidence that a checksumming script was run on the `data/` directory. The required artifact is missing, so the task is not satisfied.
- **T004** — The provided artifacts only describe research user stories for KVarN static prior and contain no configuration files, scripts, or documentation for setting up ruff linting or black formatting (e.g., no `pyproject.toml`, `.ruff.toml`, or CI integration). Consequently, the required linting/formatting setup is missing.
- **T025a** — The `stats.py` file contains a pilot analysis function, but the required output file `data/analysis/epsilon_pilot_full.json` is missing and the code shown does not write such a file. The deliverable of a generated JSON with the per‑epsilon `accumulated_kl_divergence_error_rate` has not been produced.
