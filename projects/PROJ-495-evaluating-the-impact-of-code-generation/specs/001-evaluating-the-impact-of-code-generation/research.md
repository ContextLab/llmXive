# Research: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Decision/Rationale
- **CPU‑first**: All components (Bandit, Semgrep, SonarQube via Docker, statsmodels, radon, matplotlib) run on the CPU‑only GitHub Actions runner. No GPU escape hatch is needed.
- **Statistical approach**:  
  - Vulnerability counts are typically over‑dispersed → **Negative Binomial GLM** with a `log(LOC)` offset is the primary model.  
  - Predictors: `source_group` (LLM vs. human) and `language`. A secondary model adds `complexity_proxy` and `repo_id` with **cluster‑robust SE** to address intra‑repo correlation.  
  - **Mann‑Whitney U** on per‑file corrected densities provides a non‑parametric robustness check.  
  - Two tests → **Benjamini‑Hochberg** false‑discovery‑rate correction (FR‑006).  
  - The study is **observational**; results are framed as *associational* differences (Constitution VII).  

- **Static analysis fidelity**: Bandit (Python), Semgrep (multi‑language), and SonarQube (Docker) are executed on every file; duplicate CWE findings across tools are deduplicated before counting (Principle VI).  

- **Audit‑adjusted counts**: Tool‑specific false‑positive rates are estimated from a **stratified audit sample** (minimum 10 % of findings or 200 samples, whichever is smaller, but never fewer than 100). The audit sample is **excluded** from the regression dataset to avoid circular use of the same observations.  

- **Multiple‑comparison correction**: Benjamini‑Hochberg is applied across the NB regression and Mann‑Whitney U tests, satisfying SC‑002.  

- **Power analysis**: Conducted after ingestion; if estimated power < 0.8, the limitation is documented (SC‑001).  

- **Collinearity check**: Variance Inflation Factors (VIF) are computed for all predictors; any VIF > 5 triggers a warning and the offending predictor is omitted.  

## Dataset Strategy

| Dataset | Role | Verified source |
|---|---|---|
| **CodeVulnBench** | LLM‑generated code corpus | *No verified URL – cannot be downloaded.* |
| **Juliet Test Suite** | Human‑written code corpus | *No verified URL – cannot be downloaded.* |
| **CWE taxonomy** | Mapping CWE IDs to vulnerability classes | <https://huggingface.co/datasets/mcanoglu/defect-cwe-grouping/resolve/main/test.jsonl> |
| **SonarQube results (Anticloud)** | Reference JSONL for CWE extraction (used to validate SonarQube parsing) | <https://huggingface.co/datasets/Anticloud/anticloud-sonarqube/resolve/main/ledger.jsonl> |

*Because the required CodeVulnBench and Juliet datasets lack verified URLs, the pipeline **will abort** during the ingestion phase with a clear error message. No proxy dataset is used. This limitation is recorded in `results/limitations.md` and must be resolved by providing an open, verifiable source that matches the intended LLM vs. human grouping before the primary hypothesis test can be considered conclusive.*

## Statistical Rigor Notes
- **Multiple comparisons**: Benjamini‑Hochberg across NB and Mann‑Whitney U (SC‑002).  
- **Power**: Computed via `statsmodels.stats.power` using observed `n` per group; power < 0.8 triggers a documented limitation.  
- **Over‑dispersion**: Variance/mean of raw counts inspected; if ≤ 1.5, fallback to Poisson GLM with a note.  
- **Causal framing**: Observational comparison only; no causal claims (Constitution VII).  
- **Measurement validity**: Bandit, Semgrep, SonarQube are established static analysis tools; their precision/recall will be measured via the audit (FR‑007/FR‑008, SC‑006/SC‑007).  
- **Collinearity**: VIFs calculated; high VIF predictors are omitted and the decision logged.

## Method Summary
1. **Ingest** verified CodeVulnBench and Juliet datasets → abort if unavailable.  
2. **Static analysis** (Bandit, Semgrep, SonarQube) → raw findings CSV.  
3. **Deduplicate** CWE‑identical findings across tools.  
4. **Compute LOC** (language‑agnostic) and raw density; handle zero‑LOC files as `"undefined"`.  
5. **Stratified audit** of `min(0.10 * total_findings, 200)` (≥ 100) findings, stratified by tool, CWE, and source group; audit sample is **excluded** from downstream regression.  
6. **Adjust** vulnerability counts using tool‑specific false‑positive rates derived from the audit → `corrected_vulnerability_count`.  
7. **Fit** primary NB GLM (source_group + language) with cluster‑robust SE; secondary NB GLM adds complexity and repo clustering.  
8. **Run** Mann‑Whitney U on corrected densities.  
9. **Apply** Benjamini‑Hochberg correction → adjusted p‑values.  
10. **Generate** boxplot (density) and bar chart (CWE distribution).  
11. **Store** all artifacts under `results/` for downstream paper generation (Constitution IV).  

## Expected Failure Mode
If **both** the CodeVulnBench and Juliet datasets remain unavailable (no verified URLs), the pipeline aborts early, emitting a clear error listing the missing sources. No synthetic data are fabricated; the failure prompts a spec amendment to supply verifiable open datasets.

---

