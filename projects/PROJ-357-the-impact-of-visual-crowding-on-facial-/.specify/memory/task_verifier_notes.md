# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No evidence of the required `projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/` directory or its subfolders (`code/`, `data/`, `tests/`, `artifacts/`, `state/projects/`) is provided; the implementer did not supply any file or directory listings to confirm their creation. The task remains undone.
- **T014** — declared artifact(s) missing/empty/invalid: data/interim/stimuli_manifest.json
- **T015** — No `data/interim/stimuli` image files or a `stimuli_manifest.json` file were presented, and there is no evidence that a validation script was run to check correspondence and exact parameter values. The required artifact (the manifest and its verification) is missing.
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/clutter_metrics.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/validation_report.json
- **T029** — No code, script, notebook, or data file was provided that computes per‑trial accuracy and aggregates it by stimulus ID, emotion, and flanker count. Without such an artifact, the requirement cannot be verified. The next implementer must supply the implementation (e.g., a function or script) and a sample output showing the aggregated accuracy table.
- **T027** — No evidence of `pilot_runner.py` being executed with `synthetic_data_generator.py` is provided—there are no generated raw synthetic response data files, logs, or output artifacts to confirm the pilot run was performed. The required synthetic response dataset is missing.
- **T034** — No code, script, or documentation implementing the fallback logic (detecting GLMM non‑convergence, fitting a fixed‑effects‑only model, and logging a warning) was provided; the artifact is missing entirely. The claim cannot be verified without the required implementation.
- **T035** — No code, script, function, or output implementing the Benjamini‑Hochberg FDR correction at ≤ 0.05 is present; the provided text only describes unrelated user stories and contains no artifact that demonstrates the required multiple‑comparison correction. The task therefore lacks the necessary evidence of completion.
