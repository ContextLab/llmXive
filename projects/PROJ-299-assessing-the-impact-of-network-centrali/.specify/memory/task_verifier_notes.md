# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `code/` tree (download, preprocess, centrality, analysis, viz), `tests/unit`, `tests/integration`, and `docs/` exist, but the `data/` directory contains only `.gitignore`, `__init__.py`, and `external/` — the required `data/raw`, `data/processed`, and `data/analysis` subdirectories are missing, and there is no evidence at all of the required `outputs/viz` and `outputs/reports` directories. The implementer must create these five missing subdirectories (e.g., via the existing `setup_directories.py` or manually) to satisfy the task.
- **T005** — declared artifact(s) missing/empty/invalid: code/utils/logger.py
- **T006b** — The file `code/config/network_rois.json` exists but its contents are clearly not AAL atlas-defined network assignments: DMN is simply ROIs 1–10 and FPN is ROIs 11–20, a mechanical split of the first 20 indices. The AAL atlas's DMN (e.g., precuneus, posterior cingulate, angular, medial prefrontal regions) and FPN (e.g., dorsolateral prefrontal, inferior parietal regions) map to specific, non-contiguous indices, so these lists are a placeholder rather than the explicit, correct ROI index lists the task requires. The implementer should populate the JSON with the actual AAL indices for each networ
- **T023** — declared artifact(s) missing/empty/invalid: tests/unit/test_regression.py
- **T024** — declared artifact(s) missing/empty/invalid: tests/integration/test_pipeline.py
- **T026b** — declared artifact(s) missing/empty/invalid: outputs/perf_metrics.json
