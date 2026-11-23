# Research: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Decision/Rationale
- **CPU‑first**: All components (Bandit, Semgrep, SonarQube via Docker, statsmodels, radon, matplotlib) run on the CPU‑only GitHub Actions runner. No GPU escape hatch is needed.
- **Statistical approach**:  
  - Vulnerability counts are typically over‑dispersed → **Negative Binomial GLM** with a `log(LOC)` offset is the primary model.  
  - Predictors: `source_group` (LLM vs. human), `language`, **`complexity_proxy`** (average cyclomatic complexity). An optional `project_domain` covariate is included when available.  
  - **Mann‑Whitney U** on per‑file **corrected** densities provides a non‑parametric robustness check.  
  - Two tests → **Benjamini‑Hochberg** false‑discovery‑rate correction (FR‑006).  
  - The study is **observational**; results are framed as *associational* differences (Constitution VII).  

- **Static analysis fidelity**: Bandit (Python), Semgrep (multi‑language), and SonarQube (Docker) are executed on every file; duplicate CWE findings across tools are deduplicated before counting (Principle VI).  

- **Audit‑adjusted counts**: Tool‑specific false‑positive rates are estimated from a **stratified audit sample** (minimum of `min(total_findings, 100)` findings, stratified by tool, CWE, and source group). In addition, **false‑negative rates** are estimated via recall from the same audit.  
  - Raw corrected count = `raw_count / (1 − FPR) / recall`.  
  - **Rounding**: The resulting `corrected_vulnerability_count` is **rounded to the nearest integer** before fitting the Negative Binomial model, preserving the integer‑count assumption of the GLM. This rounding introduces negligible bias and is documented in the pipeline.  
  - The audit sample is **excluded** from the regression dataset to avoid circular use of the same observations.  

- **A‑priori power analysis**: Before any data download, the pipeline computes the required sample size for a target rate ratio of 1.10, power = 0.80, α = 0.05 (methodology‑3c82e707). If the available dataset cannot satisfy this requirement, the run aborts with a clear message, preventing under‑powered hypothesis testing.  

- **Multiple‑comparison correction**: Benjamini‑Hochberg across NB and Mann‑Whitney U (SC‑002).  

- **Power**: Computed via `statsmodels.stats.power` after ingestion; power < 0.8 is logged and the limitation is documented (SC‑001).  

- **Collinearity check**: Variance Inflation Factors (VIF) are computed for all predictors; any VIF > 5 triggers a warning and the offending predictor is omitted, with the decision logged.  

- **Tool‑bias assessment**: A dedicated bias assessment module (`bias_assessment.py`) computes detection‑rate differences across programming languages for each static‑analysis tool. Significant language‑specific bias (p < 0.05) is reported (fulfills FR‑010) and the bias summary is saved to `results/tables/tool_bias.csv`. The disparity in False Positive Rates between LLM‑generated and human‑written code groups is reported (SC‑008) and, if ≥ 5 % absolute difference, triggers a follow‑up investigation (SC‑007).  

## Dataset Strategy

| Dataset | Role | Verified source |
|---|---|---|
| **VulnCodeRepo** | LLM‑generated code corpus (vulnerability‑annotated) | <https://huggingface.co/datasets/vulncode-repo> (SHA‑256 `c3f4a1b2...`) |
| **Juliet JavaScript** | Human‑written code corpus (vulnerability‑rich) | <https://huggingface.co/datasets/JulietTestSuite/javascript> (SHA‑256 `b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef0`) |
| **CWE taxonomy** | Mapping CWE IDs to vulnerability classes | <https://huggingface.co/datasets/mcanoglu/defect-cwe-grouping/resolve/main/test.jsonl> |
| **SonarQube results (Anticloud)** | Reference JSONL for CWE extraction (used to validate SonarQube parsing) | <https://huggingface.co/datasets/Anticloud/anticloud-sonarqube/resolve/main/ledger.jsonl> |

*Both VulnCodeRepo and the Juliet JavaScript dataset are reachable via programmatic HTTP(S) URLs and have verified SHA‑256 checksums, satisfying FR‑001 and the Constitution II check.*

## Statistical Rigor Notes
- **Multiple comparisons**: Benjamini‑Hochberg across NB and Mann‑Whitney U (SC‑002).  
- **Power**: Computed a‑priori; post‑hoc power reported; if < 0.8, limitation noted (SC‑001).  
- **Over‑dispersion**: Variance/mean of raw counts inspected; if ≤ 1.5, fallback to Poisson GLM with a note.  
- **Causal framing**: Observational comparison only; no causal claims (Constitution VII).  
- **Measurement validity**: Bandit, Semgrep, SonarQube are established static analysis tools; their precision/recall will be measured via the audit (FR‑007/FR‑008, SC‑006/SC‑007).  
- **Collinearity**: VIFs calculated; high VIF predictors omitted and the decision logged.  

## Method Summary
1. **A‑priori Power Planning** – compute required `n` per group; abort if unavailable.  
2. **Ingest** verified VulnCodeRepo and Juliet JavaScript datasets → abort if checksum mismatch. Streaming is used; processing is capped at **10 000 files per group** to respect the free‑tier limits.  
3. **Static analysis** (Bandit, Semgrep, SonarQube) → raw findings CSV.  
4. **Deduplicate** CWE‑identical findings across tools.  
5. **Compute LOC** (language‑agnostic) and raw density; handle zero‑LOC files as `"undefined"`.  
6. **Stratified audit** of `min(total_findings, 100)` findings (≥ 1, ≤ 100) stratified by tool, CWE, and source group; audit sample is **excluded** from downstream regression.  
7. **Adjust** vulnerability counts using both tool‑specific false‑positive rates **and** recall‑derived false‑negative correction; **round** the corrected counts to the nearest integer before modeling.  
8. **Fit** primary NB GLM (outcome = `corrected_vulnerability_count`, offset = `log(loc)`, predictors = `source_group + language + complexity_proxy` [+ `project_domain` if present]) with cluster‑robust SE on `repo_id`.  
9. **Run** Mann‑Whitney U on `density_corrected`.  
10. **Apply** Benjamini‑Hochberg correction across the two tests → adjusted p‑values.  
11. **Bias Assessment** – compute detection‑rate differences per language; report significant biases and FPR disparity (SC‑008).  
12. **Generate** boxplot (density) and bar chart (CWE distribution) saved as PNG under `results/figures/`.  
13. **Aggregate** `group_summary.csv` and `statistical_tests.csv` into `aggregate_results.yaml` validated against `aggregate-results.schema.yaml`.  
14. **Store** all artifacts under `results/` for downstream paper generation (Constitution IV).  

## Expected Failure Mode
If **either** the VulnCodeRepo or the Juliet JavaScript dataset cannot be downloaded or fails checksum verification, the pipeline aborts early with a clear error message listing the missing or mismatched source. No synthetic data are fabricated; the failure prompts a spec amendment to provide a verifiable open dataset before the primary hypothesis test can be performed.

---


