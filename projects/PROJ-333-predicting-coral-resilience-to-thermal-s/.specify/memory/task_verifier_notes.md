# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001b** — Checked the project root `projects/PROJ-333-predicting-coral-resilience-to-thermal-s` for a `.gitignore` file; the listed artifacts only include `data/raw/` and `data/processed/` directories and their contents, with no `.gitignore` present. The required file is missing, so the task is not satisfied.
- **T002** — The `requirements.txt` file is present, but it lists the required packages without version pins (e.g., `biopython` instead of `biopython==X.Y.Z`). The task explicitly demanded *pinned* dependencies, which is not satisfied.
- **T003a** — The evidence contains no `.flake8` file (or any file showing its contents) in the project root, so we cannot verify that a configuration with `max-line-length=88` and `ignore=E203,W503` was created. The required artifact is missing.
- **T004a** — The `code/config.py` file exists and defines the required constants, but the comment for `MIN_COUNT_THRESHOLD` does not match the mandated wording. It lacks the exact phrase “# MIN_COUNT_THRESHOLD=10 is a temporary placeholder. Research phase MUST update this value via T020b before final analysis.”, so the task’s specification is not fully satisfied.
- **T009b** — declared artifact(s) missing/empty/invalid: specs/001-coral-resilience-prediction/technical-design/threshold_strategy.md
- **T019b** — declared artifact(s) missing/empty/invalid: code/quant.py, data/processed/count_matrix.csv
- **T020** — declared artifact(s) missing/empty/invalid: code/quant.py, data/processed/filter_log.md
- **T023b** — declared artifact(s) missing/empty/invalid: code/batch_detection.R, data/processed/count_matrix.csv, data/raw/srr_list.json, data/processed/dge_design_config.json, data/processed/batch_detection_log.md
- **T024** — declared artifact(s) missing/empty/invalid: code/dge_analysis.R, data/processed/count_matrix.csv, data/processed/dge_design_config.json
- **T025** — declared artifact(s) missing/empty/invalid: code/dge_analysis.R, data/processed/dds.rds
- **T026** — declared artifact(s) missing/empty/invalid: code/dge_analysis.R, data/processed/dge_results.csv
- **T027** — declared artifact(s) missing/empty/invalid: code/dge_analysis.R, results/report.md
- **T028a** — declared artifact(s) missing/empty/invalid: data/processed/null_expectation.json
- **T028b** — declared artifact(s) missing/empty/invalid: data/processed/pvalue_distribution.png, data/processed/validation_report.md
- **T028c** — declared artifact(s) missing/empty/invalid: data/processed/sc002_metrics.json
- **T028d** — declared artifact(s) missing/empty/invalid: data/processed/fdr_assertion.json
- **T029** — declared artifact(s) missing/empty/invalid: data/processed/dge_results.csv
- **T032** — declared artifact(s) missing/empty/invalid: code/viz.py, data/processed/volcano_plot.png
- **T033** — declared artifact(s) missing/empty/invalid: code/gene_mapping.py, data/processed/mapped_gene_ids.txt
- **T034** — declared artifact(s) missing/empty/invalid: code/enrichment.py, data/processed/enrichment_raw.json
- **T035** — declared artifact(s) missing/empty/invalid: code/enrichment.py, data/processed/enrichment_report.md
- **T035c** — declared artifact(s) missing/empty/invalid: results/report.md
