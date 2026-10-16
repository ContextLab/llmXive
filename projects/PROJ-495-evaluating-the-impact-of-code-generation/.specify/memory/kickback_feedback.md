# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The GLM model uses covariates `source_group` and `language` only (see Summary bullet 4). This omits key confounders such as code complexity, project/domain, and file‑level clustering, risking biased estimates of the effect of LLM generation on vulnerability density.
- Static analysis runs three tools (Bandit, Semgrep, SonarQube) and aggregates CWE‑tagged counts, but the plan does not specify any deduplication or consensus procedure. Identical vulnerabilities reported by multiple tools could be double‑counted, compromising construct validity of the vulnerability density metric.
- The GLM treats each file as an independent observation. Files originating from the same repository or project are likely correlated, violating the independence assumption and inflating Type I error rates.
- Audit‑adjusted counts apply a uniform false‑positive rate derived from a stratified sample to all findings. This ignores tool‑specific false‑positive behavior and CWE‑specific variation, potentially biasing the corrected vulnerability counts.
- The LLM‑generated corpus **CodeVulnBench** is listed with **“No verified public source found”**. Without a reachable, verifiable URL the pipeline cannot download the primary dataset, making the entire analysis infeasible. The specification must be amended to reference an open, programmatically downloadable substitute (e.g., a Hugging Face dataset such as `bigcode/codeparrot` or another publicly‑available LLM‑generated code collection) and provide its verified URL and checksum.
