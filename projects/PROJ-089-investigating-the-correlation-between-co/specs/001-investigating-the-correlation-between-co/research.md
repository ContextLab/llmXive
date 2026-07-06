# Research: Investigating the Correlation Between Code Churn and Technical Debt

## Dataset Strategy

### Primary Data Sources

The analysis requires real GitHub repositories with:
1. >500 stars (to ensure active, well‑maintained projects)  
2. >2 years of commit history  
3. Support for Python, Java, JavaScript, Go, or Rust (for static analysis tool compatibility)

**Verified Datasets**:  
- No pre‑computed dataset containing both git history and static‑analysis metrics is available.  
- Consequently, the pipeline **dynamically fetches** repositories via the GitHub API and extracts metrics in real‑time.

### Data Collection Strategy

1. **Repository Selection**: Use GitHub Search API to locate repositories meeting the criteria.  
2. **Git History Extraction**: Clone each repository and employ `pydriller` to extract per‑file commit counts and lines changed over the last 2 years.  
3. **Static Analysis**:  
   - **Python** files → `radon==2.4.0` (Cyclomatic Complexity, Maintainability Index).  
   - **Other supported languages** → `semgrep` (detects code smells and computes cyclomatic complexity). *Note: SonarQube was replaced by Semgrep due to RAM constraints on the free-tier runner.*  
   - All tool versions and their GitHub star counts are recorded in `tool_validation_log.csv`.  
4. **Data Integration**: Merge git and static‑analysis metrics at the file level, producing `unified_metrics.csv`.

### Dataset Validation

For each repository the pipeline verifies:
- Presence of ≥2 years of commit history.  
- Successful execution of static analysis (logs and skips failures).  
- Files have average LOC ≥ 10 (default threshold) before metric calculation.  
- Unsupported language files are excluded.

## Statistical Methodology

### Primary Analysis: Mixed-Effects Model

To address the non-independence of files within repositories (pseudoreplication) and the "common divisor" problem:

1. **Model Specification**:  
   `debt_score ~ total_lines_changed + avg_loc + project_age + language + contributor_count + (1 | repo_id)`  
   - **Response**: `debt_score` (raw sum of complexity/smells).  
   - **Predictor**: `total_lines_changed` (raw lines).  
   - **Covariate**: `avg_loc` (controlled for, rather than used as a denominator).  
   - **Random Effect**: `(1 | repo_id)` accounts for cluster-level heterogeneity.

2. **Correlation Extraction**:  
   - Extract the partial regression coefficient for `total_lines_changed`.  
   - Compute the standardized effect (Pearson *r*) and associated p‑value from the model.  
   - Compute Spearman’s rank correlation on raw metrics as a robustness check.

### Meta‑Analysis of Repository‑Level Effects

- For each repository, compute Fisher‑transformed *r* (raw churn vs. raw debt).  
- Perform a **random‑effects meta‑analysis** across repositories to obtain an aggregate effect size and confidence interval.  
- This replaces the invalid Bonferroni correction for p‑values, correctly handling between‑repo heterogeneity and controlling the family‑wise error rate for the *set* of repositories.

### Sensitivity Analysis (FR‑008)

- Re‑run the mixed‑effects analysis with file‑size exclusion thresholds of **5, 10, and 20 LOC**.  
- Store results in `sensitivity_analysis.csv`, reporting how *r* and p‑values vary with the threshold.

### Power and Sample Size Considerations

- **Unit of Analysis**: The primary hypothesis test is at the **repository level** (N ≈ 50‑100).  
- **Power Calculation**: With 50-100 independent clusters (repos), the power to detect a moderate effect (|r| ≥ 0.3) at α = 0.05 is approximately [deferred, estimated >0.80 based on standard meta-analysis power tables]. The planned repositories satisfies this.  
- **Note**: While the total number of files is high, they are not independent observations. Power is determined by the number of clusters (repos), not files.

### Tool Validation (SC‑005)

- `tool_validation_log.csv` records for each static‑analysis tool: version, GitHub star count, and citation (e.g., Kitchenham et al., 2009).  
- The pipeline fetches the star count via the GitHub API at runtime. The system logs the *presence* of these citations but does not independently verify the *quality* of the underlying study (Constitution Principle II limitation).

## Compute Feasibility Assessment

### Resource Constraints (GitHub Actions Free Tier)

- **CPU**: Max two concurrent repo processes.  
- **Memory**: Peak ≈ 4 GB (processing one repo at a time).  
- **Disk**: < 5 GB total (raw code, intermediate files, results).  
- **Runtime**: Estimated several hours for a representative set of repositories (cloning ≈ 2 h, git extraction ≈ 1 h, Semgrep analysis ≈ 1 h, modeling [deferred]).

### Feasibility Justification

- **Semgrep** is a lightweight CLI requiring < 1 GB RAM, no server component, and runs entirely on CPU.  
- **Radon** is fast for Python files.  
- All steps are streamed or batched to stay within the 7 GB RAM limit.
- **SonarQube** was excluded as it requires a Java server instance exceeding 2GB RAM, which is infeasible on the free tier.

## Risk Mitigation (Re‑iterated)

1. **Static Analysis Failures** – Logged, repo excluded, pipeline continues.  
2. **Insufficient History** – Filtered out during selection.  
3. **Memory Exhaustion** – Process repos sequentially; use streaming.  
4. **Time Limit** – Parallelism limited to 2 processes; early exit on timeout.  
5. **Collinearity** – VIF check; if VIF > 5, apply Ridge regularization.  
6. **Methodological Validity** – Using raw metrics + covariate control avoids spurious correlation.

## Ethical Considerations

- Only public repository data is used.  
- No personally identifying information is stored.  
- All results are presented as **associational** findings, not causal claims.