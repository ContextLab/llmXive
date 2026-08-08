# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory tree or file listings were provided to confirm that the requested folders (`code/`, `code/utils/`, `tests/`, `data/raw`, `data/processed`, `data/synthetic`, `models/`, `docs/`, `docs/contracts/`, `state/projects/`) actually exist. The implementer only claimed to have run the `mkdir` command without supplying any artifact or verification output.
- **T001b** — No artifact (e.g., a terminal log, script, or repository commit) was provided to demonstrate that `chmod 555 data/raw` was actually run and that the directory now has read‑execute‑only permissions. Without such evidence the claim cannot be verified.
- **T005** — The `io_helpers.py` file is truncated – the `write_checksum_to_state` function is incomplete and does not actually write to the required `state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml` (which is also missing). Additionally, no artifact‑hashing helper is present. These missing pieces prevent the task from being fully satisfied.
- **T006** — The required file `specs/contracts/dataset.schema.yaml` is missing entirely, so no schema definition exists to verify the required fields or removal of extraneous ones. The task therefore is not satisfied.
- **T007** — The required file `specs/contracts/output.schema.yaml` does not exist (the only mentioned schema file is missing), so no schema definitions for `feature_matrix` and `model_metrics` are provided. The task’s output artifact is absent.
- **T008** — No logging configuration, code, or `logs/pipeline.log` file was provided; the claim lacks any artifact demonstrating that stdout capture, warning/mode‑switch logging, resource‑usage logging, or log‑rotation have been implemented. The required logging infrastructure is therefore missing.
- **T014** — declared artifact(s) missing/empty/invalid: state/projects/PROJ-164-neural-oscillations-as-a-biomarker-for-p.yaml
- **T016** — declared artifact(s) missing/empty/invalid: docs/research_results.md
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/epochs.fif
