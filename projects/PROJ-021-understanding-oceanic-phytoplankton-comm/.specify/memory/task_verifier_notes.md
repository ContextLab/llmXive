# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The only artifact found is `code/requirements.txt`, which correctly lists all required packages (and a few extras), but there is no evidence that the project is explicitly set up for Python 3.11 (e.g., no `pyproject.toml`, `setup.cfg`, or other version‑specifying file) nor any other initialization files (e.g., `__init__.py`, starter script). Adding a manifest that declares `requires‑python = ">=3.11"` (or equivalent) would satisfy the task.
- **T005** — The `code/utils/data_loaders.py` file exists but contains only placeholder/stub implementations that do not satisfy the task requirements. Specifically:

1. **`stream_netcdf_by_chunk()`**: Contains only a comment saying "Implementation would use xarray's open_dataset with chunks" and yields an empty `xr.Dataset()`. This is a non-functional stub, not a working streaming implementation.

2. **`sample_to_ram_limit()`**: Marked as a placeholder with no actual sampling logic—it simply returns the dataset unchanged. The task requires "sampling to fit available RAM," which is not implemented.

3. **`
- **T006** — The task requires creating two specific schema definition files in `specs/001-phytoplankton-vlm-analysis/contracts/`: `phytoplankton_sample.schema.yaml` and `model_performance.schema.yaml`. While the directory exists and contains 5 entries, the evidence explicitly shows both required files are MISSING (file does not exist). The directory contains `.gitkeep`, `aligned_dataset.schema.yaml`, and `feature_importance.schema.yaml`, but the two files specified in the task are absent. Without these schema definitions, the task is incomplete regardless of whether other schema files exist in the directo
- **T011a** — Requested task execution failed; rerun successfully: code/01_fetch_reanalysis.py exit=1
- **T011a_verify** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T020** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T050** — the task writes platform-owned path(s) inside the project: `state/projects/...yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T030** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
