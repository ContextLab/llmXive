# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory structure (`code/`, `data/raw/`, `data/derived/`, `data/results/`, `specs/`, `tests/`) is present in the provided artifacts; the claim lacks any tangible evidence that the required folders were created.
- **T004** — The `code/hygiene.py` file is truncated (e.g., `load_state_yaml` ends with a typo and the script never writes the computed hashes back to the YAML), and the required state file `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml` does not exist at all. Both the implementation and the target artifact are missing/incomplete.
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T010** — The repository contains `code/data/extract_geometry.py`, but the file is truncated and does not show a complete implementation of parsing, validation, exclusion logging, and writing to `data/derived/constraints.jsonl`. Moreover, the required output file `data/derived/constraints.jsonl` is absent. Both the artifact and its expected result are missing or incomplete.
- **T012** — The repository contains a `run_solver.py` file, but the required output files `data/derived/predictions.jsonl` and `data/derived/latency_log.jsonl` are absent, and the script lacks a complete execution flow (e.g., no main entry point, placeholder logic). Consequently the task of batch‑processing 1,000 scenes and writing the two JSONL files is not fulfilled.
- **T013** — declared artifact(s) missing/empty/invalid: data/results/exclusion_log.json
