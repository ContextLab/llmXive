# Research: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Decision/Rationale
- **CPU‑first**: All tools (Bandit, Semgrep, SonarQube via Docker, statsmodels, scipy, matplotlib, radon) run on a multi‑CPU, modest‑memory (several‑GB RAM) GitHub Actions runner. No GPU‑dependent computation is required; therefore no escape hatch is needed.  
- **Statistical approach**:  
  - Vulnerability counts are over‑dispersed → **Negative Binomial GLM** with `log(LOC)` offset (primary test).  
  - Predictors for the **primary GLM** are `source_group` (LLM vs. human) and `language` only, matching the task‑defined predictor set.  
  - A **secondary GLM** adds `complexity_proxy` (average cyclomatic complexity) and `repo_id` (project/domain proxy) and uses **cluster‑robust standard errors** clustered on `repo_id` to respect intra‑repo correlation (robustness check).  
  - **Mann‑Whitney U** on per‑file corrected densities provides a non‑parametric robustness check.  
  - Two tests → **Holm‑Bonferroni** correction (FR‑006).  
  - The study is **observational**; all statements will be framed as *associational* (Constitution VII).  
- **Static analysis tools**: Bandit (Python), Semgrep (multi‑language), and SonarQube (run via Docker) are pip‑installable / container‑runnable, run entirely on CPU, and emit CWE identifiers.  
- **Deduplication**: Identical findings reported by multiple tools for the same file/line/CWE are **collapsed** to a single record before counting, preventing double‑counting.  
- **Audit‑adjusted counts**: False‑positive rates are computed **per tool** from the manual audit sample; each tool’s findings are scaled by its own FPR before aggregation, yielding `corrected_vulnerability_count`.  

## Dataset Strategy

| Dataset | Role | Verified source |
|---|---|---|
| **The Stack (deduplicated)** (LLM‑generated code) | Primary LLM code corpus | **Verified**: <https://huggingface.co/datasets/bigcode/the-stack-dedup> |
| **Human‑written code subset** (Juliet Test Suite) | Human baseline | **Verified**: <https://github.com/secure-software-engineering/Juliet-Test-Suite> |
| **CWE taxonomy** | Mapping of vulnerability IDs to classes | **Verified**: <https://huggingface.co/datasets/mcanoglu/defect-cwe-grouping/resolve/main/test.jsonl>, <https://huggingface.co/datasets/mcanoglu/cwe-base-group/resolve/main/test.jsonl>, <https://huggingface.co/datasets/zefang-liu/cve-and-cwe-mapping-dataset/resolve/main/Global_Dataset.csv> |
| **SonarQube Community Edition** | Static analysis engine | **Verified**: Docker Hub `sonarqube:latest` (official image) |

*Note*: The only verified dataset in the provided block (the “CPU‑only parquet” file) does not contain code files or vulnerability annotations, so it is **not used**.

## Statistical Rigor Notes
- **Multiple comparisons**: Holm‑Bonferroni correction across the Negative Binomial and Mann‑Whitney U tests; adjusted α reported (SC‑002).  
- **Power**: After ingestion, we compute the detectable effect size given the observed `n` per group. If estimated power < 0.8, we note the limitation in `results/limitations.md` (SC‑001).  
- **Over‑dispersion check**: Prior to fitting NB, variance/mean of raw counts is examined; if not over‑dispersed, we fall back to a Poisson GLM and document the choice (SC‑001).  
- **Causal framing**: Observational comparison; no causality claims (Constitution VII).  
- **Measurement validity**: Bandit, Semgrep, and SonarQube are established static analysis tools; their precision/recall will be empirically estimated via the stratified audit (FR‑007/FR‑008, SC‑006/SC‑007).  
- **Collinearity**: Predictors `source_group`, `language`, `complexity_proxy`, and `repo_id` are conceptually distinct; variance inflation factors will be checked and reported.  

## Method Summary
1. **Ingest** corpora → manifest + SHA‑256 checksums (Constitution III).  
2. **Static analysis** (Bandit + Semgrep + SonarQube) → per‑file CWE‑tagged counts (Constitution VI).  
3. **Deduplication** collapses duplicate findings across tools.  
4. **LOC counting** → compute **raw density**; apply **tool‑specific false‑positive correction** → `density_corrected`.  
5. **Complexity proxy** calculation (radon) → `complexity_proxy`.  
6. **Statistical tests** →  
   - **Primary Negative Binomial GLM** with `source_group` + `language` predictors, cluster‑robust SE on `repo_id`.  
   - **Secondary Negative Binomial GLM** adds `complexity_proxy` and `repo_id`.  
   - **Mann‑Whitney U** on `density_corrected` (excluding `"undefined"`).  
   - **Holm‑Bonferroni** correction across the two p‑values → `statistical_tests.csv`.  
7. **Stratified audit** → precision/recall/FPR per tool and per group (FR‑007/FR‑008).  
8. **Visualizations** → boxplot (density) + bar chart (CWE distribution) (FR‑005).  
9. All artifacts stored under `results/` for downstream paper generation (Constitution IV).

## Expected Failure Mode
If **both** the LLM‑generated code corpus **and** the human code subset cannot be downloaded **with verified URLs**, the pipeline exits with a non‑zero status and prints a concise error listing the attempted URLs. No synthetic data are created; the failure prompts a spec amendment to provide a verifiable open dataset.  

---



