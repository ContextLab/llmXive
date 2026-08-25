# Research: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Summary

This research phase validates the feasibility of performing a meta-analysis on the relationship between structural brain connectivity (dMRI metrics) and music preferences. The primary challenge is the scarcity of direct correlation data. The research confirms that while many studies exist on "auditory processing" and "reward pathways," few directly report `(r, n)` pairs for "music preference" as a behavioral variable. Consequently, the project relies heavily on the **Systematic Review Fallback Protocol** (Constitution Principle VII) as a primary expected outcome, while still implementing the full quantitative pipeline for cases where sufficient data is found.

## Dataset Strategy

The project does **not** use a single pre-packaged dataset. Instead, it aggregates data from primary literature. The "Verified datasets" block provided in the input contains **no** direct source for "brain connectivity vs. music preference" meta-data.

| Dataset Name | Source Type | Verified URL | Relevance | Strategy |
|:--- |:--- |:--- |:--- |:--- |
| PubMed/Scopus (Literature) | Primary Literature Search | N/A (Search Engines) | **Core Source** | The system will simulate the extraction process using synthetic data that mimics real literature distributions. |
| OpenNeuro (Proxy) | Real dMRI Dataset | `https://openneuro.org/` | **High** | Used for **pipeline validation**. We will extract dMRI metrics and behavioral variables (e.g., cognitive load) to test the extraction and analysis modules against real noise, even if the behavior is not "music preference". |
| HCP (Proxy) | Real dMRI Dataset | ` | **High** | Used for **pipeline validation** (similar to OpenNeuro). |
| Skip_NoClip_Data | HuggingFace | ` | **None** | This dataset is unrelated to neuroscience. Ignored. |
| MRI-OASIS-1-IXI | HuggingFace | ` | **Partial** | Contains dMRI metrics (FA/MD) but **no** music preference data. Ignored for primary analysis, used for structural validation. |
| CT-MRI Metrics | HuggingFace | ` | **None** | CT/MRI metrics, not dMRI/behavior. Ignored. |

**Conclusion on Data Availability**: No open, programmatic dataset exists that contains the required `(tract, r, n)` pairs for "music preference."
**Decision**: The implementation must rely on **synthetic data generation** for testing and demonstration, strictly following the "Verified datasets" constraint by *not* fabricating a URL for a non-existent dataset. The `code/` will include a `generate_synthetic_literature.py` script that creates a realistic `extracted_studies.csv` based on the distributions described in the spec (e.g., varying tract names, effect sizes). This synthetic data serves as the "Raw" input for the pipeline, satisfying the "Reproducibility" requirement by being deterministic.

### Synthetic Data Generative Model
To ensure the synthetic data is not arbitrary, the `generate_synthetic_literature.py` script will use empirical parameters derived from existing dMRI meta-analyses:
- **Effect Size (r)**: Mean `r` = 0.25 (based on typical dMRI-behavior correlations in literature, e.g., *Scholz et al., 2009*).
- **Heterogeneity (tau²)**: Set to 0.04 (based on *Meyer et al., 2019* meta-analysis of FA/MD).
- **Sample Size (n)**: Log-normal distribution with median 50, range 20-200.
- **Tract Frequency**: Arcuate Fasciculus ([deferred]), Cingulum ([deferred]), Uncinate ([deferred]), Others ([deferred]).
- **Constraint**: When `--config bonferroni` is active, exactly 5 distinct tracts will be generated to satisfy SC-004.

### Proxy Data Strategy
To validate the pipeline's statistical assumptions against real-world noise, we will use **OpenNeuro** and **HCP** datasets as proxies. We will extract dMRI metrics and behavioral variables (e.g., cognitive load, anxiety) to test:
- Random-effects model convergence.
- I² calculation accuracy.
- Egger's test behavior under real heterogeneity.
This ensures the pipeline is not just a "tautology" of synthetic data.

## Statistical Methodology

### 1. Meta-Analysis Model
- **Model**: Random-Effects Meta-Analysis (DerSimonian-Laird or Restricted Maximum Likelihood).
- **Justification**: Neuroscience studies exhibit significant heterogeneity (different scanners, protocols, populations). A fixed-effects model is inappropriate.
- **Implementation**: `statsmodels.stats.meta_analysis` (Python).
- **Output**: Pooled effect size ($r_{pooled}$), 95% CI, $I^2$ statistic.
- **Disclaimer**: *Synthetic data is for pipeline integrity testing only. Scientific claims rely entirely on the (currently non-existent) real literature extraction.*

### 2. Heterogeneity Assessment
- **Metric**: $I^2$ (Percentage of total variation due to heterogeneity).
- **Thresholds**: $I^2 < 25\%$ (Low), $25-50\%$ (Moderate), $>50\%$ (Substantial).
- **Action**: If $I^2 > 50\%$, the report will highlight heterogeneity and suggest subgroup analysis (if data permits).

### 3. Publication Bias (Three-Tier Logic)
- **Test**: Egger's Linear Regression Test.
- **Gate Logic**:
 - **N < 10**: Skip test. Report "Skipped: Insufficient studies (N < 10) for Egger's regression."
 - **10 <= N < 20**: Run test. Report result **AND** a "Low Power Warning: Egger's test has low power for N < 20; results should be interpreted with caution."
 - **N >= 20**: Run test normally.
- **Visualization**: Funnel Plot (Effect Size vs. Standard Error).
- **Sensitivity**: If $I^2 > 50\%$, run **Trim-and-Fill** as an alternative bias assessment.

### 4. Multiple Comparisons
- **Correction**: **Holm-Bonferroni** (Step-down) as primary method.
- **Justification**: Tracts within a study are anatomically correlated (non-independent). Bonferroni assumes independence and is overly conservative. Holm-Bonferroni controls Family-Wise Error Rate (FWER) while being less conservative.
- **Condition**: Applied only if $N \ge 10$ AND $k \ge 2$.
- **Comparison**: Bonferroni correction will also be calculated and reported for conservative comparison.

### 5. Unit of Analysis Error (MLM)
- **Model**: Multilevel Meta-Analysis (MLM) clustering by study ID.
- **Justification**: Multiple tracts per study (k > 1) violate the independence assumption of standard random-effects models. MLM accounts for this clustering.
- **Implementation**: `metafor` (via `rpy2`) or pure Python equivalent for `rma.mv`.
- **Output**: Pooled effect size, CI, and comparison with primary Random-Effects model.

## Harmonization Protocol
Music preference is multidimensional (genre, arousal, valence, familiarity). The pipeline will:
1. **Standardize**: Convert all effect sizes to Fisher's Z for pooling.
2. **Subgroup**: If studies report distinct dimensions (e.g., "arousal" vs "valence"), treat them as subgroups in the meta-analysis.
3. **Qualitative**: If dimensions are too disparate, the study is included in the narrative synthesis but excluded from the quantitative pool.

## Computational Feasibility

- **CPU-First**: All statistical operations (meta-analysis, regression, plotting) are lightweight and run comfortably on a 2 vCPU, 7GB RAM runner.
- **No GPU Required**: No deep learning or transformer models are used for the core analysis.
- **Memory**: The maximum dataset size (even with 1000 synthetic studies) is < 1MB. Memory is not a constraint.
- **Time**: Processing 100 studies takes < 30 seconds. The 6-hour CI limit is not a concern.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data for Testing** | No verified dataset exists for the specific correlation. Using synthetic data ensures the pipeline is testable and reproducible without violating the "no fabricated URL" rule. |
| **Proxy Data for Validation** | OpenNeuro/HCP provide real dMRI noise to validate statistical assumptions (heterogeneity, convergence) against real-world data. |
| **Random-Effects Model** | Standard for meta-analysis in neuroscience where heterogeneity is expected. |
| **Three-Tier Egger's Gate** | Balances Spec requirement (N>=10) with Methodological rigor (N>=20 for reliability). The "Low Power Warning" for 10-19 ensures transparency. |
| **Holm-Bonferroni** | Corrects for dependent tracts better than Bonferroni. |
| **MLM Sensitivity** | Addresses the Unit of Analysis Error (non-independence of tracts) which is a critical methodological flaw in standard meta-analysis of tract data. |
| **N < 10 Pivot** | Mandated by the Constitution (Principle VII) and the Spec (FR-006). Prevents invalid statistical synthesis on insufficient data. |
| **Harmonization Protocol** | Ensures that disparate music preference metrics are handled consistently or excluded from the quantitative pool. |
| **Disclaimer** | Explicitly states that synthetic data is for testing only, avoiding circular validation of scientific claims. |
| **Scope Statement** | Current codebase is the SSoT; future GPU features are out of scope. |