# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires creating `code/`, `data/raw`, `data/processed`, `data/results`, `tests/`, and `utils/` directories, but the evidence only confirms `code/` and `tests/` exist — there is no evidence that any of the three `data/` subdirectories (`data/raw`, `data/processed`, `data/results`) were created, nor that `utils/` exists as a directory (it appears only as an entry inside `code/`, not at the project root as specified). The implementer must create the missing `data/raw`, `data/processed`, `data/results`, and root-level `utils/` directories (with `.gitkeep` markers if empty) to satisfy the
- **T002** — The `requirements.txt` exists but contains a typo `rdkkit` (the correct package is `rdkit`, so the dependency would fail to install) and none of the required packages (`rdkit`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `tqdm`, `huggingface_hub`, `matplotlib`, `seaborn`, `scipy`) are pinned to versions as the task requires. Fix the typo and add version pins for all specified dependencies.
- **T003** — No artifacts were provided or found on disk for this task — there is no `pyproject.toml`, `ruff.toml`, `.ruff.toml`, `setup.cfg`, or any configuration file containing `ruff` or `black` settings, nor any evidence (e.g., lint/format run output) that the tools were configured or executed. The task requires actual configuration of linting and formatting tools; with zero artifacts to inspect, the claim cannot be verified and must be treated as not done.
- **T004** — The evidence collector lists no artifacts for this task — there is no `utils/memory_monitor.py` (or any resolved equivalent) present on disk, so the claimed RAM-tracking/downsampling module cannot be verified to exist, let alone implement the ≥ 6.5 GB trigger with ≤ 7 GB peak behavior. The implementer must actually create the module (with memory monitoring and a graceful downsampling mechanism) and provide evidence of its content/execution.
- **T005** — The evidence collector lists no artifacts on disk for this task — there is no confirmed `utils/parsers.py` (or any resolved equivalent path) in `projects/PROJ-301-predicting-molecular-descriptors-from-qu`, and no execution evidence (e.g., tests of SMILES conversion, XYZ parsing, or malformed-molecule error handling). With no file present and no content to inspect, the claimed implementation cannot be verified; the implementer must actually create `utils/parsers.py` with the SMILES/XYZ conversion functions and error handling, and provide evidence it runs.
- **T011** — declared artifact(s) missing/empty/invalid: code/03_sampling.py, data/processed/molecules_cleaned.parquet, data/processed/split_indices_final.json, data/processed/
- **T018** — declared artifact(s) missing/empty/invalid: code/04_train_orchestrator.py, code/train_2d.py, code/train_3d.py
- **T017** — declared artifact(s) missing/empty/invalid: code/04_aggregate_metrics.py
- **T021** — declared artifact(s) missing/empty/invalid: code/05_analysis.py, data/processed/labels_test.csv
- **T022** — declared artifact(s) missing/empty/invalid: code/05_analysis.py, data/processed/labels_test.csv
- **T023** — declared artifact(s) missing/empty/invalid: code/05_analysis.py
- **T025** — declared artifact(s) missing/empty/invalid: code/05_analysis.py
- **T026** — declared artifact(s) missing/empty/invalid: code/05_analysis.py
- **T024** — declared artifact(s) missing/empty/invalid: code/05_analysis.py
- **T027** — declared artifact(s) missing/empty/invalid: code/05_analysis.py
- **T041** — declared artifact(s) missing/empty/invalid: tests/integration/test_full_pipeline.py
