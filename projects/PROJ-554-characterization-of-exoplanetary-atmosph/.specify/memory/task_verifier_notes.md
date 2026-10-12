# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — Checked the repository tree under `projects/PROJ-554-characterization-of-exoplanetary-atmosph/`. The `code/`, `tests/`, and `results/` directories are present, but the required `data/` directory is missing. The task’s specification explicitly calls for a `data/` folder, so the directory structure is not fully created.
- **T001b** — Checked `projects/PROJ-554-characterization-of-exoplanetary-atmosph/requirements.txt`. The file lists the required packages but does **not** include pinned version specifiers (e.g., `petitRADTRANS==1.2.3`), violating the task’s explicit demand for pinned versions. Additionally, extra unrelated packages are present, but the primary failure is the lack of version pins. The implementer must add exact version numbers for each listed dependency.
- **T006a** — declared artifact(s) missing/empty/invalid: data/raw/, data/processed/
- **T013a** — Requested task execution failed; rerun successfully: code/download.py exit=1
- **T029** — declared artifact(s) missing/empty/invalid: results/plots/water_vs_temp.png, results/plots/residuals.png, results/plots/correlation_matrix.png, results/plots/noise_vs_signal.png
- **T055** — declared artifact(s) missing/empty/invalid: tests/integration/test_reproducibility.py
- **T038** — declared artifact(s) missing/empty/invalid: results/results_summary.md
