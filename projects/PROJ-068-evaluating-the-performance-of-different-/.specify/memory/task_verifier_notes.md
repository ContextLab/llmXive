# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`projects/PROJ-068-evaluating-the-performance-of-different-/code/`, `tests/`, `data/`, `results/`) or of the `tools/setup_verify.py` script execution is present; the claim is unsupported by any actual artifacts.
- **T007** — No evidence of the required `data/processed/` and `results/benchmarks/` directories, the `tools/pre-commit-checksum.py` script, or the git hook symlink is provided. The implementer did not supply the artifacts needed to satisfy task T007.
- **T006** — The repository contains `code/benchmarks/generator.py`, but the file is truncated and does not include logic to stream generated samples to `data/processed/` as CSVs nor to write SHA‑256 checksums to `data/checksums.manifest`. Moreover, the required `data/checksums.manifest` file is absent. Consequently, the task’s full requirements are not satisfied.
- **T025** — declared artifact(s) missing/empty/invalid: results/benchmarks/consistency_report.json
