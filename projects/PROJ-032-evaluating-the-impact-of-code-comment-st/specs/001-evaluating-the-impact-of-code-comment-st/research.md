# Research: Evaluating the Impact of Code Comment Style on Maintainability

## 1. Research Question
Does the style of code comments (readability, sentiment, density, and variance) correlate with software maintainability proxies (code quality degradation, issue-linked bug rate) in Python projects, controlling for project size, age, and complexity?

## 2. Dataset Strategy

| Variable | Source | Verified URL / Loader | Status |
| :--- | :--- | :--- | :--- |
| **Repository Identifiers** | `codeparrot/github-code` (HF) | **NO VERIFIED SOURCE FOUND** in provided block. The provided block lists `notune/fable5-repos`, `nothingiisreal/Human_Stories`, and `nothingiisreal/Reddit-Dirty-And-WritingPrompts`. | **BLOCKING FLAW** |
| **Source Code** | GitHub (via clone) | `git clone https://github.com/<owner>/<repo>.git` | N/A (Derived from IDs) |
| **Git History** | GitHub (via clone) | `git clone` (full history) | N/A (Derived from IDs) |

**Decision & Rationale**:
The project specification mandates the use of the `codeparrot/github-code` HuggingFace dataset to identify repositories. However, the provided `# Verified datasets` block **does not contain a verified URL or loader for this dataset**.
*   **Implication**: Per the strict rules of the planning agent and Constitution Principle II (Verified Accuracy), we cannot invent a URL or proceed with an unverified source.
*   **Action**: The study is **BLOCKED**. Execution logic in `fetch.py` will halt with a clear error message if the verified URL is not present in the configuration. The study cannot proceed until a verified URL is added to the block or the spec is updated to use a verified dataset.

## 3. Methodology

### 3.1 Data Acquisition
1.  **Identifier Selection**: Query `codeparrot/github-code` (if verified) for Python repos with ≥100 stars. Target: A sufficiently large set of unique IDs.
2.  **Cloning**: Clone repositories in batches of 10 to manage memory (FR-013). Store in `data/raw/`.
3.  **Validation**: Verify `git log` accessibility. Skip failures. Log exclusions.

### 3.2 Metric Computation
1.  **Comment Extraction**: Use `tree-sitter-python` to parse files. Extract comments (AST nodes). Ignore string literals (FR-002).
2.  **Readability**: Calculate Flesch-Kincaid using `textstat` (FR-003).
    *   *Edge Case*: If no comments, score = 0.
    *   *Consistency*: Calculate `std_dev` of readability scores per repo.
3.  **Sentiment**: Calculate polarity using `TextBlob` (FR-004).
    *   *Consistency*: Calculate `variance` of sentiment scores per repo.
4.  **Churn**: Analyze `git log` for lines added/removed per commit (FR-005).
5.  **Code Quality Degradation Rate**: 
 * *Sampling Strategy*: To ensure feasibility within 6h/7GB RAM, run `pylint` only on the **latest commit** and a **random sample of [deferred] of commits** (stratified by merge commits).
    *   *Metric*: Ratio of sampled commits with error-level warnings.
    *   *Construct Validity*: Explicitly labeled as "Code Quality Degradation Rate" to avoid confusion with "Bug Fix Rate".
    *   *Secondary Proxy*: If issue tracker data is available, calculate "Issue-Linked Bug Rate" (commits fixing issues labeled 'bug').
6.  **Validation (FR-006, SC-002)**:
    *   Generate a manually labeled subset of N=50 commits from a reference repository.
    *   Compare automated metric against manual labels.
    *   Generate `validation_report.json` with accuracy metrics.

### 3.3 Statistical Analysis
1.  **Model**: Multiple Linear Regression (via `scikit-learn`) as mandated by Constitution Principle VII. Use Robust Standard Errors (Huber-White) to handle heteroscedasticity.
2.  **Predictors**: Readability (Mean), Sentiment (Mean), Density, Readability (Std Dev), Sentiment (Variance).
3.  **Controls**: Total Lines of Code (LOC), Project Age (Years), Cyclomatic Complexity (FR-014).
4.  **Correction**: Apply Benjamini-Hochberg FDR to p-values (FR-009).
5.  **Sensitivity**: Sweep thresholds {0.01, 0.05, 0.1} (FR-010). Output results as an array in the final JSON.
6.  **Framing**: All results reported as "associational correlations" (FR-008).

## 4. Power Analysis
*   **Sample Size**: N = 500 repositories.
*   **Predictors**: 5 predictors (Readability, Sentiment, Density, Std Dev, Variance) + 3 controls (LOC, Age, Complexity) = 8 total predictors.
*   **Alpha**: 0.05.
*   **Power Calculation**: Using G*Power logic for F-test in multiple regression (fixed model, R² deviation from zero).
    *   For N=500, k=8, α=0.05:
    *   **Medium Effect Size (f² = 0.15)**: Power ≈ 0.99.
    *   **Small Effect Size (f² = 0.02)**: Power ≈ 0.45.
*   **Conclusion**: The study is well-powered to detect medium-to-large effect sizes. It has limited power to detect small effect sizes. Results will be interpreted with this limitation in mind, and a null result is a valid and expected outcome.

## 5. Compute Feasibility
*   **CPU Only**: `textstat`, `TextBlob`, `pylint`, `scikit-learn` run on CPU.
*   **Memory**: Batch cloning (10 repos) ensures <7 GB RAM (FR-011).
*   **Time**: A time limit enforced by CI. 
 * **Sampling**: Commit sampling for `pylint` ([deferred] + latest) reduces runtime from O(Total Commits) to O(Sampled Commits), ensuring feasibility.

## 6. Risk Assessment
*   **Dataset Gap**: The lack of a verified URL for `codeparrot/github-code` is a critical blocker. The study halts until resolved.
*   **Git Clone Failures**: Private repos or rate limits may reduce the sample size below 500.
*   **Runtime**: Cloning 500 repos with full history may exceed 6 hours if network is slow. Mitigation: Use commit sampling for static analysis.
