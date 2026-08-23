# Research: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Domain Overview

This study aims to quantify the relationship between white matter integrity (measured via Diffusion MRI metrics like Fractional Anisotropy or Mean Diffusivity) in specific neural tracts and individual differences in music preference. The hypothesis is that structural connectivity in the "auditory-reward pathway" (e.g., arcuate fasciculus, uncinate fasciculus) correlates with the intensity or type of music preference.

## Methodological Strategy

### Meta-Analysis Approach
1.  **Data Extraction**: Extract correlation coefficients (`r`), sample sizes (`n`), and tract identifiers from eligible studies.
2.  **Statistical Synthesis**: Use a **random-effects model** (DerSimonian-Laird or REML) to pool effect sizes, accounting for between-study heterogeneity.
3.  **Heterogeneity**: Calculate **I²** to quantify the percentage of variance due to heterogeneity.
4.  **Publication Bias**: Perform **Egger's linear regression test** to detect asymmetry in funnel plots.
    -   **Gate**: N >= 20 for reliable detection.
    -   **Caveat**: If 10 <= N < 20, report the result with a "Low Power" warning.
    -   **Skip**: If N < 10.
5.  **Multiple Comparisons**: Apply **Bonferroni correction** for multiple tract comparisons if N >= 10 and k >= 2 (Primary Analysis).
6.  **Robustness Check**: Perform **Multilevel Meta-Analysis (MLM)** to account for the clustering of tracts within studies (Secondary Analysis).

### Fallback Strategy
If the number of eligible studies (unique Author-Year pairs) is < 10:
-   **Pivot**: Switch to a **Narrative Systematic Review**.
-   **Output**: Generate a structured text summary of qualitative findings regarding "neural circuitry" and "preference" without quantitative aggregation.

## Literature Extraction Protocol

Since no single public dataset exists for this specific correlation, the system relies on a defined extraction protocol to generate the input `studies.csv`.

### Search Strategy
-   **Databases**: PubMed, Web of Science, Scopus.
-   **Search Strings**: 
    -   `("diffusion MRI" OR "dMRI" OR "fractional anisotropy" OR "mean diffusivity") AND ("music preference" OR "music liking" OR "musical taste")`
    -   `("structural connectivity" OR "white matter") AND ("music" OR "auditory") AND ("preference" OR "liking")`
-   **Inclusion Criteria**:
    -   Primary studies reporting a direct correlation (r) or test statistic (t, F) between dMRI metrics and music preference.
    -   Studies reporting sample size (n).
    -   Studies identifying specific brain tracts.
-   **Exclusion Criteria**:
    -   Review articles, editorials, non-human studies.
    -   Studies without extractable effect sizes.

### Effect Size Conversion
If studies report only p-values, t-statistics, or F-statistics without direct `r`:
-   **t-to-r**: `r = sqrt(t^2 / (t^2 + df))` where `df = n - 2`.
-   **F-to-r**: `r = sqrt(F / (F + df))` where `df` is the error degrees of freedom.
-   **Directionality**: If the study reports a one-tailed test, convert to two-tailed `r` if possible, or exclude if ambiguous.
-   **Error Propagation**: The variance of the converted effect size will be calculated using standard formulas (e.g., `var(r) = (1 - r^2)^2 / (n - 1)`).

## Dataset Strategy

**Constraint**: The project requires a dataset containing specific dMRI metrics (FA/MD) and behavioral music preference ratings.
**Reality Check**: No verified dataset in the public domain contains the specific pairing of **structural brain connectivity metrics** AND **music preference ratings**.
-   `mri-oasis-1-ixi-pre` contains MRI data but is a structural/functional dataset for general brain segmentation, not music preference.
-   `pubmed-summarization` contains text abstracts, not statistical effect sizes.

**Resolution Plan**:
1.  **Primary Strategy**: The implementation is designed to accept a **CSV input** generated via the **Literature Extraction Protocol** above. The pipeline is agnostic to the source of this CSV.
2.  **Simulation for CI**: To satisfy the "Independent Test" requirements in the spec (US-1, US-2) and demonstrate functionality on the GitHub Actions runner, the pipeline will include a **mock data generator** that creates synthetic studies with known parameters. **This mock data is strictly for code validation and does not answer the research question.**
3.  **Real Data Handling**: If a real dataset is provided in `data/raw/studies.csv`, the pipeline will process it. If the dataset is missing or insufficient (N < 10), the fallback logic will trigger.
4.  **No Fabrication**: The plan does NOT fabricate a dataset URL. It relies on the `data/raw` directory being populated with a valid CSV (either by a manual researcher upload following the extraction protocol or a separate extraction script).

## Statistical Rigor & Feasibility

-   **CPU Feasibility**: Meta-analysis of <100 studies is computationally trivial on a 2-core CPU. `statsmodels` and `scipy` are lightweight and fit well within 7GB RAM.
-   **Multiple Comparisons**: Bonferroni correction will be applied strictly as per FR-005.
-   **Collinearity**: If a study reports multiple tracts from the same cohort, the plan will treat them as distinct comparisons for Bonferroni (primary) but will use MLM to account for the dependency (robustness).
-   **Power Limitation**: The system explicitly acknowledges that N < 10 is underpowered for Egger's test and Bonferroni correction, triggering the fallback. For Egger's, N >= 20 is preferred for reliability.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Random-Effects Model** | Essential for meta-analysis of neuroscience studies which inherently vary in methodology and population. |
| **N < 10 Fallback** | Prevents invalid statistical synthesis (Type I errors) when data is scarce, satisfying FR-006. |
| **Hybrid Bonferroni + MLM** | Satisfies the spec's mandate for Bonferroni (FR-005) while addressing the Unit of Analysis Error via MLM. |
| **Mock Data for CI** | Since no verified dataset exists for this specific correlation, mock data is required to test the pipeline logic without fabricating scientific claims. |
| **CPU-First** | Statistical aggregation is not GPU-intensive; CPU execution ensures compatibility with free-tier runners. |