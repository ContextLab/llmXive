# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `src/`, `tests/`, or `data/` directory (or any files within them) was provided; the only material shown is a feature specification, not the required project structure. The implementer must create and show the three top‑level directories with appropriate placeholder files to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or CI integration scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The claim provides only high‑level feature specifications and user stories; there is no code, script, or documentation implementing an error‑handling wrapper for data loading and model inference, nor any tests demonstrating a “FAIL LOUDLY” policy without synthetic fallbacks. The required artifact (the wrapper implementation) is missing.
- **T011** — declared artifact(s) missing/empty/invalid: src/data/embeddings.py
- **T012** — The provided `src/cli.py` is truncated and does not contain the logic to save embeddings to `data/processed/embeddings/` nor to write the complexity scores CSV. Moreover, the required `data/processed/complexity_scores.csv` file is absent from the repository. These missing artifacts mean the pipeline does not fulfill the stated requirement.
- **T013** — declared artifact(s) missing/empty/invalid: data/processed/failed_subjects.log
- **T016** — The provided `src/cli.py` is truncated and does not contain any code that iterates over the target dimensions (16, 32, 64, 128, 256) or writes aggregated logs to `data/processed/sweep_logs.json`. Moreover, the required `data/processed/sweep_logs.json` file is absent from the repository. Both the orchestrating script and its output are missing, so the task is not satisfied.
- **T017** — The provided `src/cli.py` defines a timeout‑checking function, but the script never invokes it (no call after T016 and before T019) and it does not hard‑code the required output path `data/results/pipeline_timeout.json`. Moreover, the expected JSON log file is absent. The task’s requirement to abort the job and write that specific file is therefore not satisfied.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/failed_subjects.log
