# Research: Quantifying the Impact of Code Authorship Diversity on Software Security

## 1. Problem Statement

The project investigates whether code authorship **breadth** (measured by **unique author count**) is associated with a lower count of software vulnerabilities (CVEs). The hypothesis is that diverse authorship introduces more rigorous code review and reduces "bus factor" risks, leading to fewer security flaws.

**Note on Metric Definition**: The primary independent variable is **`unique_authors`** (count), not `unique_authors / KLOC`. The ratio `unique_authors / KLOC` is calculated for descriptive purposes only. Using the ratio as a predictor while simultaneously including `log(KLOC)` as a covariate in the model creates a mathematical tautology (collinearity) that invalidates the causal interpretation. The model tests the effect of **author count** while controlling for **project size** (`log(KLOC)`).

## 2. Dataset Strategy

### 2.1 Target Repositories
The study requires a list of public GitHub repositories. A curated list of popular open-source projects will be used as the target population.
* **Source**: GitHub API (public list).
* **Verification**: Verified via GitHub API reachability.
* **URL**: ` (Query: `language:Python+stars:>1000` or similar curated list).

### 2.2 Vulnerability Data (NVD)
Vulnerability records are sourced from the National Vulnerability Database (NVD).
* **Source**: NVD CVE JSON Feeds.
* **Verification**: The NVD provides a public API and JSON downloads.
* **URL**: `https://nvd.nist.gov/vuln/data-feeds` (Official NVD feed page).
* **Access**: Public, no credentials required. The plan downloads specific yearly JSON files to stay within disk limits.
* **Matching Strategy**: **Substring Matching** between the GitHub repository URL and the `references` field in the NVD JSON.
 * *Rationale*: Strict exact URL matching (as per FR-002 text) often fails because NVD references point to specific release tags, issue trackers, or vendor advisories, not the root repository URL. Substring matching (e.g., checking if the repo URL is contained within the reference URL) mitigates this construct validity threat and prevents massive false negatives that would bias the outcome variable towards zero for mature projects. Ambiguous matches are logged and excluded.
 * *Bias Mitigation*: A stratified random sample of matches will be manually verified to estimate the false-positive rate. A sensitivity analysis will re-run the model excluding the top proportion of projects with the most CVE matches to assess stability.

### 2.3 Code Metrics (Authorship & Size)
* **Source**: Local Git clones of the target repositories.
* **Method**:
 * **Author Count**: `git log --format='%ae'` (or `%an`) executed on the repository.
 * **Constraint**: To ensure historical depth while respecting CI limits, the clone uses `--shallow-since=2015-01-01`. This captures all commits from the last decade, sufficient for most active projects, and avoids the `--depth=1` trap which only sees the latest commit.
 * **KLOC**: Calculated using `cloc` on the same snapshot.
* **Feasibility**: Cloning a representative set of repositories with a 10-year history is feasible on the 14GB disk limit if managed sequentially and cleaned up after processing.

## 3. Statistical Methodology

### 3.1 Model Specification
The primary analysis uses a **Negative Binomial Generalized Linear Model (GLM)**.
* **Outcome**: `cve_count` (integer count of CVEs). **Note**: `cve_density` is explicitly excluded from the model formula.
* **Predictors**:
 * `author_count` (Primary variable of interest; **breadth**).
 * `project_age` (Years since first commit).
 * `primary_language` (One-hot encoded via `scikit-learn` `OneHotEncoder`).
 * `release_count` (Number of GitHub releases).
 * `log(kloc)` (Natural log of code size, included as a **free predictor** per FR-004 Spec Amendment).
* **Formula**: `cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)`
* **Causal Assumption Justification**: `log(kloc)` is treated as a **confounder** (project size drives both author count and CVE count), not a mediator. The hypothesis is that diversity reduces CVEs *independently* of size. If `kloc` were a mediator, the estimate would represent only the direct effect. This distinction is explicitly reported.

### 3.2 Robustness Checks
* **Subsampling**: Fit the model separately for subsets of repositories grouped by primary programming language (e.g., Python, Java, C++) to check for language-specific effects.
* **Alternative Metric (Evenness)**: Replace `unique_authors` with **Shannon Entropy** of author commit contributions.
 * *Distinction*: `unique_authors` measures **breadth** (number of contributors), while Entropy measures **evenness** (distribution of contributions). These are distinct hypotheses. 'Diversity' is defined as Breadth for the primary test.
* **Distributional Assumptions (Categorical Binning)**: Treat `author_count` as a categorical factor (binned into groups: 1, 2-5, 6-10, 10+) to test for non-linear effects and zero-inflation.
* **Zero-Inflated Negative Binomial (ZINB)**: A ZINB model will be fitted. If the ZINB model's AIC/BIC is significantly lower than the standard Negative Binomial, the ZINB results will be reported as the primary robustness finding, and the continuous assumption will be flagged as insufficient.
* **Collinearity Handling**: If VIF > 5, the plan will automatically switch to **Ridge Penalized Negative Binomial regression** with the penalty parameter selected via cross-validation. The Ridge coefficients will be reported as the primary result for that subsample.

### 3.3 Multiple Testing Correction
* **Method**: Benjamini-Hochberg (BH) procedure.
* **Scope**: Applied to all raw p-values generated from the main model and all robustness checks.
* **Output**: A single global table of adjusted p-values.

### 3.4 Statistical Rigor & Assumptions
* **Over-dispersion**: Negative Binomial is chosen specifically because vulnerability counts are typically over-dispersed (variance > mean), violating Poisson assumptions.
* **Collinearity**: `log(kloc)` and `author_count` may be correlated. The model will report Variance Inflation Factors (VIF). **If VIF > 5, the plan will automatically switch to Ridge Penalized Negative Binomial regression** (using `glmnet` or `statsmodels` with penalty) with the penalty parameter selected via cross-validation.
* **Causal Claims**: The study is **observational**. Claims will be framed as "associations" or "correlations," not causal effects.
* **Power**: With a sufficient number of observations, the study has sufficient power to detect moderate effect sizes, provided the number of CVEs is not zero-inflated beyond the Negative Binomial's capacity.
* **Distributional Assumptions**: A robustness check treating `author_count` as a categorical factor (binned) will be performed regardless of model convergence to test for skew/zero-inflation effects. **Additionally, a Zero-Inflated Negative Binomial (ZINB) model will be fitted. If ZINB AIC/BIC is significantly lower, ZINB results will be reported as the primary robustness finding.**

## 4. Compute Feasibility

### 4.1 CPU-First Strategy
* **Cloning**: `git clone` is I/O bound but CPU light. Sequential processing ensures memory safety (<7GB RAM).
* **Statistics**: `statsmodels` runs efficiently on CPU for N=500. No GPU required for GLM fitting.
* **Data Processing**: Pandas operations on a 500-row dataset are instantaneous.
* **Disk**: A large number of repos * ~10MB average = substantial total storage. Fits within 14GB limit. NVD JSON files (streamed or partial) fit within remaining space.

### 4.2 GPU Escape Hatch
* **Not Required**: This project does not involve deep learning, transformers, or large-scale matrix factorization that requires a GPU. The "GPU escape hatch" is not needed for this specific methodology.

## 5. Data Availability & Integrity

* **NVD Feed**: Verified as open and downloadable. The plan includes a checksum verification step (`sha256`) to ensure data integrity (Constitution Principle III).
* **GitHub Repos**: Publicly accessible. No authentication required for read-only access to public repos.
* **No Synthetic Data**: The plan strictly forbids synthetic data generation. If a repo cannot be cloned or matched, it is excluded and logged.

## 6. Decision Rationale

* **Why Negative Binomial?** Vulnerability counts are sparse and over-dispersed. Poisson GLM would underestimate standard errors.
* **Why `--shallow-since`?** `--depth=1` (as proposed in T008) is insufficient for calculating `unique_authors` for repositories with history >1 commit. `--shallow-since` provides the necessary historical depth while respecting CI disk limits. **Constitution Amendment Required**.
* **Why `log(kloc)` as covariate?** Treating size as an offset assumes a fixed ratio of CVEs per line of code, which is empirically false. Including it as a covariate allows the model to estimate the independent effect of size while controlling for it.
* **Why Substring Matching?** Exact URL matching results in massive false negatives. Substring matching is a valid heuristic to improve construct validity without introducing significant false positives.
* **Why ZINB?** To address the excess zeros in the data distribution which standard NB might not capture.
* **Why Ridge Regression?** To provide stable estimates in the presence of high multicollinearity (VIF > 5).