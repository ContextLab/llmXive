# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — No `main.py` file or any code was presented, and there is no evidence of an orchestrator implementing error handling or timeout logic. The required artifact is missing, so the task is not satisfied.
- **T010** — No `data_extraction.py` script or any code implementing the GitHub API query, star/age/language filtering, or repository cloning is present in the provided evidence. Without the required artifact, the task’s specification is not satisfied.
- **T011** — No `data_extraction.py` script is present, nor any evidence of cloned repositories or CSV output containing per‑file commit counts and lines changed for the last two years. The required artifact is missing, so the task is not satisfied.
- **T012** — declared artifact(s) missing/empty/invalid: data/raw/repos_metadata.csv
- **T013b** — No `utils.py` file or any code implementing the required validation logic (checking for the two named tools or a star count >5,000 and logging the result) was presented. The artifact is missing, so the task is not satisfied.
- **T014** — No `static_analysis.py` script or any code implementing the described radon and semgrep integration is provided; without the file we cannot verify that CC, MI, code smells are computed or that a `debt_score` is calculated as specified. The required artifact is missing.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/unified_metrics.csv
- **T018** — No `analysis.py` script or any code showing loading of `unified_metrics.csv`, VIF calculation for `project_age`, `language`, `contributor_count`, or conditional Ridge regression is provided. The required artifact is missing, so the task is not satisfied.
- **T023** — declared artifact(s) missing/empty/invalid: data/results/correlation_results.csv, data/results/sensitivity_analysis.csv, data/results/meta_analysis_results.csv
