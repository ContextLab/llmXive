# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The log shows that a virtual environment was created and `pip install -r requirements.txt` was executed, but it does not include the resulting `pip list` output (or the contents of `data/venv_setup_done.txt`) to prove that all required packages were installed with the exact versions specified. Without that evidence the verification step is missing.
- **T004** — Requested task execution failed; rerun successfully: code/run_lint.py exit=1
- **T010** — Checked `code/config_loader.py` (3541 bytes). It loads variables from a `.env` file (or defaults) but never reads `.env.example`, so it does not meet the requirement to load placeholder keys from that file. The import runs without error, but the core functionality is incomplete.
- **T055b** — the task writes platform-owned path(s) inside the project: `state/projects/...yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T015** — declared artifact(s) missing/empty/invalid: code/data/download_auditory.py
- **T016** — declared artifact(s) missing/empty/invalid: code/data/download_visual.py
- **T016a** — declared artifact(s) missing/empty/invalid: code/data/checksums.py, state/projects/PROJ-779-cross-modal-comparison-of-neural-predict.yaml, state/...yaml
- **T017** — declared artifact(s) missing/empty/invalid: code/data/download_auditory.py
- **T018** — declared artifact(s) missing/empty/invalid: code/data/download_visual.py
- **T036a** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T040** — declared artifact(s) missing/empty/invalid: code/analysis/stats_permutation.py
- **T041** — declared artifact(s) missing/empty/invalid: code/analysis/stats_ttest.py
- **T042** — declared artifact(s) missing/empty/invalid: code/analysis/stats_tost.py
- **T043** — declared artifact(s) missing/empty/invalid: code/analysis/stats_bh.py
- **T043b** — declared artifact(s) missing/empty/invalid: code/analysis/stats_bh.py, data/results/bh_corrected_pvalues.json
- **T049** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T057** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T059** — declared artifact(s) missing/empty/invalid: docs/deviation-sc-002.md
