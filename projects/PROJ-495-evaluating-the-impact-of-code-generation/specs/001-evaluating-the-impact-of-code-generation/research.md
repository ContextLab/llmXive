# Research: Evaluating the Impact of Code Generation on Code Vulnerability Density

## Decision/Rationale
- **CPU‑first**: All tools (Bandit, Semgrep, SonarQube via Docker, statsmodels, scipy, matplotlib) run on a multi‑CPU, modest‑memory (several‑GB RAM) GitHub Actions runner. No GPU‑dependent computation is required; therefore no escape hatch is needed.
- **Statistical approach**:  
  - Vulnerability counts are over‑dispersed → **Negative Binomial GLM** with `log(LOC)` offset (primary test).  
  - **Mann‑Whitney U** on per‑file corrected densities provides a non‑parametric robustness check.  
  - Two tests → **Holm‑Bonferroni** correction (FR‑006).  
  - The study is **observational**; all statements will be framed as *associational* (Constitution VII).  
- **Static analysis tools**: Bandit (Python), Semgrep (multi-language), and SonarQube (run via Docker) are pip‑installable / container‑runnable, run entirely on CPU, and emit CWE identifiers.  
- **Audit‑adjusted counts**: False‑positive rates derived from the manual audit are used to correct raw vulnerability counts before density calculation (addressing construct validity).  

## Dataset Strategy

| Dataset | Role | Verified source |
|---|---|---|
| **CodeVulnBench** (LLM‑generated code) | Primary LLM code corpus | **No verified public source found** – the spec must be amended to provide an open, programmatically downloadable substitute (e.g., a Hugging Face dataset) before the pipeline can run. |
| **Human‑written code subset** (e.g., Juliet Test Suite) | Human baseline | **Verified**: |
| **CWE taxonomy** | Mapping of vulnerability IDs to classes | **Verified**: <https://huggingface.co/datasets/mcanoglu/defect-cwe-grouping/resolve/main/test.jsonl>, <https://huggingface.co/datasets/mcanoglu/cwe-base-group/resolve/main/test.jsonl>, <https://huggingface.co/datasets/zefang-liu/cve-and-cwe-mapping-dataset/resolve/main/Global_Dataset.csv> |
| **SonarQube Community Edition** | Static analysis engine | **Verified**: Docker Hub `sonarqube:latest` (official image) |

*Note*: The only verified dataset in the provided block (the “CPU‑only parquet” file) does not contain code files or vulnerability annotations, so it is **not used**.

## Statistical Rigor Notes
- **Multiple comparisons**: Holm‑Bonferroni correction across the Negative Binomial and Mann‑Whitney U tests; adjusted α reported (SC‑002).  
- **Power**: After ingestion, we compute the detectable effect size given the observed `n` per group. If estimated power < 0.8, we note the limitation in `results/limitations.md` (SC‑001).  
- **Over‑dispersion check**: Prior to fitting NB, variance/mean of raw counts is examined; if not over‑dispersed, we fall back to a Poisson GLM and document the choice (SC‑001).  
- **Causal framing**: Observational comparison; no causality claims (Constitution VII).  
- **Measurement validity**: Bandit, Semgrep, and SonarQube are established static analysis tools; their precision/recall will be empirically estimated via the stratified audit (FR‑007/FR‑008, SC‑006/SC‑007).  
- **Collinearity**: Only a single binary predictor (`source_group`) plus covariates (language, LOC, complexity proxy) are included; no collinearity concerns.  

## Method Summary
1. **Ingest** corpora → manifest + SHA‑256 checksums (Constitution III).  
2. **Static analysis** (Bandit + Semgrep + SonarQube) → per‑file CWE‑tagged counts (Constitution VI).  
3. **LOC counting** → compute **raw density**; apply audit‑derived false‑positive correction → `density_corrected`.  
4. **Statistical tests** → NB GLM (with covariates) or Poisson fallback, Mann‑Whitney U, Holm‑Bonferroni correction → `statistical_tests.csv`.  
5. **Stratified audit** → precision/recall/FPR per group (FR‑007/FR‑008).  
6. **Visualizations** → boxplot (density) + bar chart (CWE distribution) (FR‑005).  
7. All artifacts stored under `results/` for downstream paper generation (Constitution IV).

## Expected Failure Mode
If **both** the CodeVulnBench LLM dataset **and** the human code subset cannot be downloaded **with verified URLs**, the pipeline exits with a non‑zero status and prints a concise error listing the attempted URLs. No synthetic data are created; the failure prompts a spec amendment to provide a verifiable open dataset.

---



