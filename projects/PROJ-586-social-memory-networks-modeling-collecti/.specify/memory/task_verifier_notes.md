# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The only artifact present is the `requirements.txt` file; there is no evidence of a Python virtual environment being created (e.g., a `venv/` directory, `pyproject.toml`, `Pipfile.lock`, or a `pip freeze`/`requirements.txt` generated after installation). Without a concrete virtual environment and installed packages, the task “initialize Python virtual environment and install dependencies” is not fulfilled.
- **T004** — The provided `code/data/loaders.py` does not attempt to call `gymnasium.make('hanabi-v0')` or `datasets.load_dataset('coqa')`, nor does it log errors or write a `data/verification_status.json` file with the required schema. Additionally, the `data/verification_status.json` file is absent. The task’s verification and output requirements are therefore unmet.
- **T004c** — The `loaders.py` file only defines a synthetic‑fallback flag and raises a `KeyError`; it never invokes the T004b synthetic generator, does not tie fallback to a failed verification step, and does not log `[FALLBACK] Synthetic cues generated for dataset [NAME]` to `experiment.log`. Consequently the required fallback logic is not implemented.
- **T011** — Requested task execution failed; rerun successfully: code/run_experiment.py exit=1
- **T029** — declared artifact(s) missing/empty/invalid: projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json
