# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required `projects/PROJ-064-statistical-discrepancies-in-publicly-av/` directory tree (with `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`, `config/`) is provided; the claim cannot be verified without the actual filesystem artifacts.
- **T004** — I looked for the required directory structure (`data/raw/`, `data/processed/`, and `state/`) under the specified project path, but no such folders or any evidence of their creation were provided. The implementer did not supply any artifacts confirming the directories exist, so the task is not satisfied.
- **T005** — No code files, scripts, or documentation were presented showing a logging implementation in the `code/` directory, nor any evidence of JSON‑formatted logs with the required keys or a `--verify-reproducible` command‑line flag. The required artifact is missing, so the task is not satisfied.
- **T009a** — declared artifact(s) missing/empty/invalid: github/workflows/verify_reproducible.yml
- **T029** — The required output file `data/processed/null_distributions.json` does not exist, and the provided `code/simulation.py` snippet is truncated before any Monte Carlo loop or chunked‑processing logic that would produce the 10,000‑iteration simulation and write the JSON file. Both the artifact and its behavior are missing.
