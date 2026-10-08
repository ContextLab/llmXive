# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory `projects/PROJ-591-neuromorphic-transformer-networks-spikin/` (or its contents) is provided; without a visible project structure we cannot confirm the task was fulfilled. The implementer must supply the actual folder and its files to verify compliance.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings) or installation scripts are present in the provided evidence, so the requirement to configure ruff and Black is not demonstrated. The implementer must add the appropriate configuration files and ensure the tools are set up in the project.
- **T004** — The `dataset_loader.py` exists but lacks the required 3‑retry logic for the S3 fallback and never writes the computed SHA‑256 checksum to `state/projects/PROJ-591-neuromorphic-transformer-networks-spikin.yaml`, which is missing entirely. These omissions mean the task’s data‑hygiene requirement is not satisfied.
- **T005** — The file defines a 2‑layer, 4‑head transformer with roughly the right size, but it contains no logic that enforces CPU‑only execution (e.g., device checks, warnings, or forced `torch.device('cpu')`). Hence the implementation does not fully satisfy the task’s requirement.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/baseline_metrics.csv
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/spiking_metrics.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/results/sensitivity_analysis.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/results/statistical_analysis_report.md
