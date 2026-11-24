# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/pending/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T002** — The repository contains a `pyproject.toml` with the required Black configuration, but there is no `.flake8` file present and no evidence (e.g., command output or CI logs) that `flake8 --config .flake8 .` and `black --check .` both succeed. Add a `.flake8` file with appropriate defaults and provide proof that both linting and formatting checks pass.
- **T003** — the task writes platform-owned path(s) inside the project: `state/pending/checksums.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T004** — All required schema files (`dataset.schema.yaml`, `descriptor.schema.yaml`, `analysis_output.schema.yaml`, `correlation.schema.yaml`, `flexibility.schema.yaml`, `output.schema.yaml`) are missing from `specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/`, causing the `pytest` validation test to fail. The task’s core deliverables are absent.
- **T005** — Requested task execution failed; rerun successfully: code/data/retrieval.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/data/preprocessing.py exit=1
