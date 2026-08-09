# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — The required output file `data/raw/github_issues_raw_api.parquet` does not exist, and the provided `fetch_issues.py` snippet does not show any enforcement of the ≥100 repository minimum or the full fallback logic (HF validation → API fallback → loud failure). Both the missing artifact and the likely missing enforcement mean the task is not genuinely completed.
- **T011** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_issues.csv
- **T012** — declared artifact(s) missing/empty/invalid: data/logs/preprocessing.log
- **T045** — The repository enrichment script exists but is truncated (e.g., `fetch_repo_metadata` ends abruptly) and no `data/processed/repo_metadata.json` file was generated. Both the full implementation and the required output artifact are missing.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/outlier_report.json
- **T025** — No artifact (e.g., script, results table, or figure) showing a parametric bootstrap sensitivity analysis with the specified cutoffs {, 0.05, 0.1} and reporting the stability proportion is present. The claim lacks any concrete output, code, or data to verify that the analysis was performed. The required evidence is missing.
