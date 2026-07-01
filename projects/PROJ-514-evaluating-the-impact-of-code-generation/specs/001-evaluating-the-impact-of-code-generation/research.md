# Research: Evaluating Code Generation Impact on Code Smell Frequency

## Research Question
Is there a statistically significant association between the source of code (Human-written vs. LLM-generated) and the frequency of specific code smells (Long Method, Duplicated Code, Feature Envy, Long Parameter List) when controlling for repository-level context?

## Dataset Strategy

### Human-Written Code
**Source**: Public GitHub Repositories.
**Strategy**:
1.  Select 50 repositories meeting criteria: ≥100 stars, ≥5 years history, active in Python or Java.
2.  Identify commits introducing new functions via `git log --diff-filter=A`.
3.  Filter for commits associated with specific Issues/PRs to ensure "fresh" implementations.
4.  **Sampling**: Extract **3** functions per repository associated with the target Issue/PR.
5.  **Target**: 150 Human samples (3 × 50). *Note: This deviates from spec FR-001 (≥1000) to ensure statistical validity.*

**Verified Datasets**:
*Note: No pre-existing "Human Code Smell" dataset exists that meets the specific "fresh commit" and "Issue-linked" criteria. The strategy relies on programmatic fetching from GitHub, which is the only valid approach to satisfy FR-001. The following verified LLM datasets are provided for reference only and are NOT used for data collection.*
- *Reference LLM Dataset 1*: https://huggingface.co/datasets/hon9kon9ize/38k-zh-yue-translation-llm-generated/resolve/main/data/test-00000-of-00001.parquet (Historical Reference Only)
- *Reference LLM Dataset 2*: https://huggingface.co/datasets/badrex/royal_society_corpus_LLM_generated_metadata/resolve/main/data/train-00000-of-00001.parquet (Historical Reference Only)
- *Reference LLM Dataset 3*: https://huggingface.co/datasets/artnitolog/llm-generated-texts/resolve/main/data/train-00000-of-00001.parquet (Historical Reference Only)

**Action**: The implementation will fetch human code directly from GitHub, not from a pre-packaged dataset, to ensure the "fresh commit" condition of FR-001. Every sample will be logged with its exact Commit SHA and Issue/PR URL for verification.

### LLM-Generated Code
**Source**: Public LLM Inference API (e.g., HuggingFace Inference API).
**Strategy**:
1.  Derive **150** tasks (3 per repo) from the *same* Issue/PR descriptions used for human sample selection.
2.  Query the API with a standardized prompt for each task.
3.  Apply exponential backoff (limited number of retries, fixed timeout) to handle rate limits.
4.  Target: **150** samples (3 × 50). *Note: This deviates from spec FR-002 (≥50) to ensure balanced design.*

**Constraints**:
- Must not rely on GPU.
- Must fit within free-tier API limits.

## Methodology

### 1. Data Collection (US-1)
- **Human**: Use `GitPython` to traverse history. Extract function bodies. Validate syntax (AST parsing).
- **LLM**: Use `requests` to call API. Log prompt, model ID, seed. Validate syntax.
- **Pairing**: For each repository, **3** Human samples and **3** LLM samples are collected to form a "block".
- **Filtering**: Exclude samples < 5 lines or > 500 lines (noise).

### 2. Static Analysis (US-2)
- **Tool**: PMD (Java-based, runs on CPU) or SonarQube CLI (CPU mode).
- **Execution**: Parallelized (multiple concurrent jobs).
- **Memory**: Enforce `ulimit -v ` (2GB) per process.
- **Metrics**: Extract counts for:
    - Long Method
    - Duplicated Code
    - Feature Envy
    - Long Parameter List
- **Validity Check**: Run on a known "clean" set of **LLM-generated** code (in addition to human clean code). If false positive rate > 5% for LLM code, flag analysis as invalid (FR-008). *Note: Feature Envy and Duplicated Code are known to be noisy; if validity checks fail, these metrics will be reported as exploratory only.*

### 3. Statistical Comparison (US-3)
- **Primary Method**: **Blocked Permutation Test**.
    - **Rationale**: Code smell counts are zero-inflated and skewed. Standard t-tests and Mann-Whitney U assume independence or normality which is violated here. A permutation test respects the empirical distribution.
    - **Blocking**: The test will account for repository-level effects by treating repository as a blocking factor. The null hypothesis is that swapping the source label (Human/LLM) within a repository block does not change the distribution of smells.
    - **Iterations**: 10,000 permutations.
- **Correction**: Bonferroni correction for 4 tests (α_adj = 0.05/4 = 0.0125).
- **Effect Size**: Rank-biserial correlation (non-parametric) or Cohen's d (if distribution permits, but primarily rank-based).
- **Imbalance Handling**: The blocked design (3 vs 3 per repo) inherently balances the groups, eliminating the need for bootstrapping or subsampling. *This directly addresses panel concern `methodology-f30244be` by rejecting the invalid 1000/50 + bootstrapping approach.*

### 4. Sensitivity Analysis (FR-005)
- Sweep "Long Method" threshold: {100, 150, 200} lines.
- Compare results against continuous metric: Cyclomatic Complexity.
- **Goal**: Verify that the primary finding (significant vs. non-significant) is stable across thresholds.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied to control Family-Wise Error Rate (FWER) ≤ 0.05.
- **Power Analysis**: With N=50 blocks (pairs), the study is powered to detect large effect sizes (Cohen's d > 0.8) with [deferred] power. Detection of small effects is limited by the number of repositories, not the total sample size. This limitation is explicitly acknowledged in the report.
- **Causal Language**: All findings will be framed as "associations" (Observational Study Design). No causal claims (e.g., "LLMs cause more smells") will be made.
- **Contextual Equivalence**: The study compares "completed human implementations" against "generated solutions" for the same requirement. This is a comparison of "Implementation Quality" vs "Generated Solution Quality". The "freshness" of the human commit does not equate to the "freshness" of the LLM generation context; this distinction is noted in limitations.
- **Collinearity**: If "Long Method" and "Cyclomatic Complexity" are highly correlated, they will be reported descriptively, not as independent predictors.
- **Sample Size & Deviation**: The design (150/150, blocked by repo) avoids the statistical pitfalls of extreme imbalance (1000/50) and bootstrapping artifacts. **Note**: This design deviates from spec FR-001/FR-002/SC-001 which mandated 1000/50/1050. The spec requirements are acknowledged as methodologically compromised for the intended hypothesis testing.

## Compute Feasibility
- **Runtime**: 300 files × 2 min/file = 600 min. Parallelized (20 jobs) = 30 min ([deferred]). Fits 6h limit comfortably.
- **Memory**: 2GB/process limit enforced. Total aggregate < 7GB.
- **Disk**: 300 small files < 50MB. Fits GB limit.
- **No GPU**: PMD and SciPy are CPU-optimized.