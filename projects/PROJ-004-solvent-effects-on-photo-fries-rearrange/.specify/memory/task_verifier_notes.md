# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The `requirements.txt` exists but lists all packages without pinned versions (e.g., bare `numpy`, `scipy`) and omits the required `rdkit`, while adding unrequested packages (`pymatgen`, `matplotlib`, `seaborn`). The task explicitly required pinned versions of the eight named packages including `rdkit`.
- **T002b** — The `requirements.txt` at `projects/PROJ-004-solvent-effects-on-photo-fries-rearrange/requirements.txt` contains only numpy, scipy, pandas, scikit-learn, pyyaml, pymatgen, matplotlib, seaborn, pymc, and statsmodels — `rdkit` is not listed at all. The task's sole requirement was to pin `rdkit==2023.9.1` (or latest) in `requirements.txt`, so the fix is simply to add a pinned `rdkit` entry.
- **T005** — The file exists and `log_environmental_params`/`log_operation` do record parameter dicts, but the structured-logging setup is broken: `EnvironmentalFormatter.format` calls `datetime.now(timezone.utc)` while `timezone` is never imported (`from datetime import datetime` only), so any use of `setup_logging(log_file=...)` — the actual structured/file-logging path — raises `NameError` on the first record, directly contradicting the module's "never raises" contract. Fix the import (e.g., `from datetime import datetime, timezone`) and verify the formatter path executes; also note the decorator form o
- **T017c** — declared artifact(s) missing/empty/invalid: code/analysis/hash_manager.py, solvents.yaml, state/artifact_hashes.yaml
- **T015f** — declared artifact(s) missing/empty/invalid: code/data/capture.py, data/raw/kinetic_traces/
- **T017b** — declared artifact(s) missing/empty/invalid: code/analysis/compliance.py, data/processed/compliance_report.json
- **T022** — declared artifact(s) missing/empty/invalid: data/processed/kinetic_metrics.csv
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/sensitivity_analysis.csv
- **T059b** — declared artifact(s) missing/empty/invalid: data/processed/study_power_analysis.json
- **T029a** — declared artifact(s) missing/empty/invalid: data/compute/dft_results.csv
- **T029d** — declared artifact(s) missing/empty/invalid: data/chemicals/phenyl_benzoate.smi
- **T029c** — declared artifact(s) missing/empty/invalid: data/compute/solvent_solvation.csv
- **T031b** — declared artifact(s) missing/empty/invalid: data/processed/vif_raw_scores.json
- **T030b** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.json
- **T034** — declared artifact(s) missing/empty/invalid: paper/figures/regression_plot.png
- **T045** — declared artifact(s) missing/empty/invalid: code/analysis/calibration_protocol.py, data/chemicals/calibration_standards.yaml, data/processed/calibration_certificates/
- **T039** — declared artifact(s) missing/empty/invalid: tests/integration/test_full_pipeline.py
