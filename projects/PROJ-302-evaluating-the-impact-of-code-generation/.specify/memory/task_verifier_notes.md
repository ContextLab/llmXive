# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The skeleton directories (`code/`, `data/`, `tests/`, `docs/`) exist, but `requirements.txt` does not pin exact versions for all listed packages (e.g., scikit‑learn, statsmodels, scipy, radon, transformers, torch, matplotlib, seaborn, codecarbon, datasets are missing or only mentioned in a comment). No evidence is provided that `pip install -r requirements.txt` runs successfully in a fresh virtual environment. The task therefore remains incomplete.
- **T014** — The repository contains the instrumentation module `code/runtime.py`, and the verification script runs without error, but the required output file `data/processed/runtime_report.json` is missing and there is no evidence that it includes a `stage_times` entry for every listed stage or that `total_seconds` ≤ 21600. Additionally, integration of the recorder with the actual pipeline entry point is not demonstrated.
- **T002** — Requested task execution failed; rerun successfully: code/data_acquisition.py exit=1
