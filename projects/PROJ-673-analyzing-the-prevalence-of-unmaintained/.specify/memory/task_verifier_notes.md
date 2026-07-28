# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No code, configuration, or data files were presented that create a local cache in `data/raw/`, nor any implementation that computes and stores immutable checksums for raw API responses. The required artifact (caching mechanism) is missing entirely.
- **T013** — declared artifact(s) missing/empty/invalid: src/services/github_client.py
- **T016** — declared artifact(s) missing/empty/invalid: src/cli/collect_data.py
- **T017** — No code, script, dataset, or output file was provided that shows the `age_in_days` calculation logic or the handling of null `release_date` values. Consequently, there is no evidence that rows with missing release metadata have `age_in_days` set to null while still retaining a non‑null `vulnerability_count`. The required artifact is missing.
- **T021a** — The required file `data/processed/power_analysis_notes.md` does not exist, so no documentation of power assumptions or sample size justification is present. The task’s core deliverable is missing.
- **T025** — No code, script, or report artifact was provided that demonstrates the addition of logic to detect p < 0.05 and flag statistical significance in the output report, as required by US‑2 Acceptance 3. The implementer’s claim cannot be verified without such evidence.
- **T033** — No `docs/` directory or `quickstart.md` file was presented; the claim of documentation updates cannot be verified because the required artifacts are missing. The task specifically requires a `quickstart.md` in `docs/` describing how to run the pipeline, which is absent.
