# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The required file `projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/requirements.txt` does not exist, so the task’s primary artifact is missing despite a similarly‑named file being present elsewhere. The missing file must be created at the specified path with the listed dependencies.
- **T003** — No configuration files (e.g., `pyproject.toml`, `.flake8`, `.isort.cfg`) or scripts setting up Black, Flake8, and isort are present in the provided evidence, so we cannot confirm that linting and formatting tools have been configured as required. The task lacks the necessary artifacts to verify completion.
- **T004** — No `config.py` file or its contents were provided; thus there is no evidence of constants for seeds, the required bit‑widths (2‑6), or any path configurations being defined. The required artifact is missing.
- **T005** — declared artifact(s) missing/empty/invalid: data/loader.py
- **T005a** — declared artifact(s) missing/empty/invalid: data/downsampler.py, data/derived/kinetics_4s_subset_v1.parquet
- **T005b** — declared artifact(s) missing/empty/invalid: data/downsampler.py
- **T007a** — No `simulation/quantization_emulator.py` file or its contents were supplied for review, so we cannot confirm that the required stochastic rounding and integer quantization modes (with a factory function for bit‑widths 2‑6) have been implemented. The necessary artifact is missing.
- **T007b** — declared artifact(s) missing/empty/invalid: data/results/kl_divergence_per_bitwidth.json
