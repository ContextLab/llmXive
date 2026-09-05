# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree or file listings were provided, so we cannot verify that the `projects/PROJ-404-predicting-molecular-surface-charge-dist/` hierarchy was created nor that `__init__.py` files exist in each `code/` subdirectory. The required artifacts are missing from the evidence.
- **T056a** — The loader contains a SHA‑256 helper but the `update_state_checksum` function is only a placeholder and never writes to a YAML file, and the required `state/projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml` does not exist at all. Consequently the checksum is never recorded as required.
- **T058** — The provided `code/train.py` contains placeholder loss computation and does not compute or log any gradient L2 norms after `loss.backward()`. Moreover, the required output file `artifacts/reports/gradient_norms.log` is missing entirely. Hence the task’s specification is not satisfied.
