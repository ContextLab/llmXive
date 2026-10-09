# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — The required file `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` is missing (the only file found is under `specs/001-comparative-analysis-of-molecular-finger/data-model.md`). Moreover, the schemas in the existing document do not match the task’s specified fields for Compound, Fingerprint, Model, and PerformanceMetric. The implementer must create the correctly‑named markdown file and define the exact schemas as listed in the task.
- **T001a** — The required project directory `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/` does not exist, so the mandated sub‑folders (`data/raw`, `data/processed`, `code`, `tests`) are absent. The task’s core deliverable is missing.
- **T001b** — The evidence includes a `requirements.txt` and `pyproject.toml`, but the requirements file does not pin exact versions for the listed packages (and adds an unexpected `scipy` entry), and there is no `README.md` file present at all. These omissions mean the task’s specification is not fully satisfied.
- **T002** — Checked `requirements.txt` (contains only package names, no version pins) and `pyproject.toml` (present). No `README.md` file was found. The task required a pinned `requirements.txt` for the listed packages and a README, both of which are missing or incorrect.
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/filter_log.txt
- **T029a2** — declared artifact(s) missing/empty/invalid: data/processed/test_set_descriptive.json
- **T029a3** — declared artifact(s) missing/empty/invalid: data/processed/research_results.md
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
