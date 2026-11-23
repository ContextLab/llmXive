# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — The evidence shows that only `data/raw/` and `contracts/` directories exist; the required `data/cleaned/`, `data/results/`, and `figures/` directories are missing.
- **T003** — Checked the provided `pyproject.toml`, which correctly contains Black settings with `line-length = 88`. No `create.flake8` (or equivalent `.flake8`) file was found in the project artifacts, so the required linting configuration is missing. Adding a `create.flake8` file with `max-line-length = 88` and `extend-ignore = E203` will satisfy the task.
- **T038** — The provided `research.md` documents the conflict but does not contain the required exact sentence: “Constitution VII is overridden by FR-010 for this project; thermal data MUST be sourced exclusively from peer-reviewed literature or NIST, NOT Materials Project thermal endpoint.” Adding this explicit statement is needed to satisfy T038.
- **T006** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T014b** — Requested task execution failed; rerun successfully: code/src/ingest/fetch_thermal.py exit=1
- **T031a** — declared artifact(s) missing/empty/invalid: src/analysis/citation_verifier.py, data/results/final_report.md
- **T031b** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T031c** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T032** — declared artifact(s) missing/empty/invalid: data/results/feature_importance.csv
- **T033** — declared artifact(s) missing/empty/invalid: figures/
- **T034** — declared artifact(s) missing/empty/invalid: docs/performance.md
- **T035** — declared artifact(s) missing/empty/invalid: docs/quickstart.md, docs/api.md
- **T036** — declared artifact(s) missing/empty/invalid: tests/unit/test_edge_cases.py
- **T040** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T044** — declared artifact(s) missing/empty/invalid: data/results/model_metrics.json, figures/
- **T049** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
