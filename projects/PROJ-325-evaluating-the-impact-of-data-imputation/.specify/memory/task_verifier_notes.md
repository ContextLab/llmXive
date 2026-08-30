# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004** — The provided `code/data/loader.py` only parses arguments and calls external helper functions; it does not enforce the required URL, perform cache fallback, verify the `weight`, `psu`, and `strata` columns, abort on missing columns, or log to `state/manifest.yaml`. Moreover, the expected output files (`data/raw/cache/GSS2018.dta`, `data/raw/gss_2018_subset.csv`, and `state/manifest.yaml`) are absent. The task’s core functional and artifact requirements are therefore not met.
- **T004b** — declared artifact(s) missing/empty/invalid: data/raw/gss_2018_subset.csv, state/manifest.yaml
- **T005** — The repository contains a partially‑implemented `code/data/synthetic.py`, but the required output files `data/processed/synthetic_mar_v1.csv` and `data/processed/synthetic_mar_v1_meta.json` are absent, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) does not exist. Consequently the generator does not produce the mandated artifacts, so the task is not fulfilled.
- **T005b** — declared artifact(s) missing/empty/invalid: data/processed/synthetic_mar_v1.csv, data/processed/synthetic_mar_v1_meta.json, state/manifest.yaml
- **T020** — The required `data/processed/baseline_results.json` file does not exist, and neither `code/main.py` nor `code/imputation/run_all.py` contain code that writes a baseline results dictionary to that path with the required keys (`mean`, `variance`, `status` = "success", `design_type`). The task’s serialization step is therefore missing.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/psu1_warnings.json
