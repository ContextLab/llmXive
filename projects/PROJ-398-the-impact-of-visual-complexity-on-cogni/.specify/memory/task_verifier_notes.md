# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T074** — The required output file `data/derived/individual_metric_correlations.csv` does not exist, and the provided `src/metrics/validate.py` is truncated before the correlation‑computing logic is shown, giving no proof that per‑metric Pearson correlations are actually calculated and saved. The task’s core artifact is missing.
- **T020** — No code, test, or documentation was provided showing that the system sets `object_count = 0` for images where the object detector finds no objects. The required artifact (e.g., updated detection pipeline, unit test, or example output) is missing, so the requirement is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/metrics.csv
- **T018a** — No evidence of a `tests/data/` directory (or any files within it) was provided; the claim lacks any visible artifact showing isolated test data directories have been created. The required folder structure is missing, so the task is not satisfied.
- **T032a** — The required `data/metadata/dataset_manifest.json` file is missing, so no dataset version, source URL, or checksum manifest has been recorded as specified. The task’s core artifact does not exist.
- **T032b** — The provided `src/experiment/verify_clips.py` is truncated (ends mid‑line) and does not contain a complete implementation that writes the required `data/metadata/clip_manifest.json`. Moreover, the manifest file itself is missing from the repository. Both the script and its output artifact are absent or incomplete, so the task requirements are not met.
- **T032c** — declared artifact(s) missing/empty/invalid: src/experiment/curate_clips.py, data/processed/curated_clips.csv, data/metadata/curated_manifest.json
- **T028a** — The repository contains a fully‑featured `src/experiment/rt_mechanism.py` that implements timing, stimulus handling, and response capture, but the required output artifact `data/derived/rt_measurements.json` is absent. The task explicitly demands that this JSON file be generated, so the implementation is not considered complete until the script creates and writes the measurements to that path.
- **T028b** — declared artifact(s) missing/empty/invalid: src/experiment/baseline_enforcer.py
- **T028** — declared artifact(s) missing/empty/invalid: src/experiment/tasks.py
- **T029** — declared artifact(s) missing/empty/invalid: src/experiment/server.py
- **T030** — No code, script, configuration, or documentation was provided that shows logic to detect and flag records lacking TLX (NASA‑TLX) or RT (reaction‑time) values. Without an artifact demonstrating the added flagging mechanism, the requirement cannot be confirmed as met.
