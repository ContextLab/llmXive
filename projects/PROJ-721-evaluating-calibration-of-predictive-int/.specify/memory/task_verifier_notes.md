# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided artifact only shows top‑level entries (e.g., `code/`, `data/`, `results/`, `tests/`) but does not demonstrate that the required sub‑directories (`data/raw`, `data/processed`, `results/plots`, `tests/unit`, `tests/integration`, `tests/contract`, `state`) actually exist. A full recursive listing (`ls -R`) confirming each of these paths is missing.
- **T002** — The provided `requirements.txt` exists and lists all required packages, but it does not pin them to exact versions (it uses `>=` specifiers) as the task demands, and there is no evidence that `pip check` was run to confirm conflict‑free installation. The implementer must supply a `requirements.txt` with exact version pins (e.g., `statsmodels==0.14.0`) for every listed dependency and include proof that `pip check` passes.
- **T004** — The listed evidence shows that `data/raw/` does not contain `M4-Dataset.zip` (file missing) and `state/checksums.yaml` is also missing, so the required artifacts are absent and the checksum validation cannot be performed. The implementer must add the downloaded zip file and the checksum YAML file.
- **T004b** — The provided `config.yaml` is present but its contents do not match the specification: the required top‑level keys `learning_rate`, `step_size`, `initial_alpha`, `seed` are missing or nested under `aci`/`pipeline`; `nominal_levels` contains `[0.80, 0.90]` instead of `[0.80, 0.95]`; and `sensitivity_thresholds` lacks the value `0.02`. The file therefore fails the verification script.
- **T005a** — declared artifact(s) missing/empty/invalid: code/models/arima_model.py, tests/unit/test_models.py
- **T005b** — declared artifact(s) missing/empty/invalid: code/models/ets_model.py, tests/unit/test_models.py
- **T005c** — declared artifact(s) missing/empty/invalid: code/models/prophet_model.py, tests/unit/test_models.py
- **T005d** — The required file `code/models/lightgbm_quantile.py` is missing, and the test file `tests/unit/test_models.py` (which contains the verification test) does not exist, so no implementation or test can be run. The task’s core artifact is absent.
- **T010** — declared artifact(s) missing/empty/invalid: tests/unit/test_metrics.py
- **T013a-2** — declared artifact(s) missing/empty/invalid: data/processed/sample_indices.csv, state/sampling_metrics.json
- **T017a** — declared artifact(s) missing/empty/invalid: results/hypotheses_list.json
- **T017d** — declared artifact(s) missing/empty/invalid: results/pvalues.json, results/hypotheses_list.json
- **T025** — declared artifact(s) missing/empty/invalid: results/stratified_coverage.csv
- **T026** — declared artifact(s) missing/empty/invalid: results/plots/stratified_bar.png
- **T041** — declared artifact(s) missing/empty/invalid: results/bootstrap_pvalues.json, results/recalibration_pvalues_fdr.json
- **T031** — declared artifact(s) missing/empty/invalid: results/recalibration.csv
- **T034b** — declared artifact(s) missing/empty/invalid: results/memory.log, scripts/profile_memory.py
