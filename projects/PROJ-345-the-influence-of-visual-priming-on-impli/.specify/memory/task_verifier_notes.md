# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The `pyproject.toml` is present and correctly configures ruff and black, but the required `.pre-commit-config.yaml` file is missing, so the pre‑commit hook configuration cannot be verified or installed. The task is therefore not fully satisfied.
- **T007** — The generated `state/projects/PROJ-345/state.yaml` does not contain the required top‑level keys `project_id`, `created_at`, and `artifact_hashes`; instead it has unrelated fields. Moreover, the `init_state.py` script writes to `state/PROJ-345/state.yaml` (missing the required `projects/` subdirectory), so it would not create the file at the specified location. The correct schema and path are therefore not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/linked_trials.csv
- **T018** — declared artifact(s) missing/empty/invalid: state.yaml
- **T022b** — No code, data, or output artifacts were provided; the claim contains only a description of user stories unrelated to the “Human‑Rated Ambiguity Verification Gate” task, and there is no evidence that any required script, model, or report was created. The required deliverables are missing.
- **T041** — No new unit test files are present in the `tests/unit/` directory, and there is no evidence of tests covering the specified edge cases (missing metadata, high collinearity). The required additional tests are missing, so the task is not satisfied.
- **T043** — No evidence of a `quickstart.md` validation run is provided—there are no logs, reports, or any artifact showing that the quickstart instructions were executed and reproduced end‑to‑end. Consequently the requirement is not satisfied.
