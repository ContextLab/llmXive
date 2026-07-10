# Research: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Summary

This research phase investigates the feasibility of a meta-analysis on the correlation between structural brain connectivity (dMRI metrics) and music preferences. The primary challenge is the scarcity of direct (r, n) pairs in existing literature. The strategy prioritizes a quantitative random-effects meta-analysis if ≥10 eligible studies are found; otherwise, it pivots to a narrative systematic review.

**Scientific Validity & Construct Validity**:
The project distinguishes between **Pipeline Validation** (using synthetic data to test code logic) and **Scientific Discovery** (analyzing real data).
1. **Synthetic Data**: Used *only* to verify that the code correctly calculates pooled effects, I², and Egger's test. The "ground truth" is known by design. This does *not* validate the hypothesis that "dMRI correlates with music preference."
2. **Real Data**: If real studies < 10, the system **must** output a narrative review. No quantitative pooled estimate is valid if the data is sparse or heterogeneous.

## Verified Datasets

The following datasets are available and verified for use. Note that **no dataset directly contains "music preference" ratings paired with dMRI metrics**. The analysis will rely on extracting data from primary studies (via PubMed abstracts) or using proxy datasets for methodological testing.

| Dataset Name | URL | Relevance |
|--------------|-----|-----------|
| PubMed Abstracts | ` | Primary source for extracting study metadata and qualitative descriptors. |
| PubMed Q&A | ` | Potential source for structured question-answer pairs regarding neural circuitry. |
| Psychedelics Pubmed | ` | Irrelevant (wrong domain). |
| FOMO260K MRI | ` | Contains MRI mappings but lacks behavioral/music data. Useful for testing dMRI metric parsing. |
| FOMO45K MRI | ` | Same as above. |
| Brain MRI Dataset | ` | Contains MRI metadata but no music preference data. |

**Dataset Strategy**:
1. **Unit Testing**: Generate synthetic CSV with known `r`, `n`, and tract names to test pipeline logic (recovery of ground truth).
2. **Real-World Extraction**: The `extraction.py` module will parse PubMed abstracts.
 - *Quantitative*: Extract `r` and `n` ONLY if explicitly stated in text. If missing, the study is **excluded** from the quantitative pool.
 - *Qualitative*: Extract tract names and directional descriptors using regex (see below).
3. **Fallback**: If extraction yields <10 studies with valid (r, n), the system triggers the narrative synthesis mode.

## Methodological Decisions

### 1. Statistical Model (Random-Effects)
- **Decision**: Use a random-effects model (DerSimonian-Laird or REML) via `statsmodels` or `scipy`.
- **Rationale**: Studies in neuroscience vary widely in methodology, scanners, and populations. A random-effects model accounts for between-study heterogeneity, which is expected to be high.
- **Reference**: Constitution Principle VI mandates this approach.

### 2. Heterogeneity (I²)
- **Decision**: Calculate I² statistic.
- **Precision**: Must be reported to **at least two decimal places** (addressing T019).
- **Threshold**: I² ≥ 50% indicates substantial heterogeneity (US-2).
- **Heterogeneity Handling**: If I² > 75% or data is extremely sparse, the pooled estimate will be flagged as "unreliable" in the output report, and the narrative description will be prioritized.

### 3. Publication Bias (Egger's Test)
- **Decision**: Perform Egger's linear regression test.
- **Condition**: **ONLY** if N ≥ 10 (number of studies).
- **Skip Message**: If N < 10, output `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression."` (addressing T021).

### 4. Multiple Comparisons (Bonferroni)
- **Decision**: Apply Bonferroni correction for multiple tract comparisons.
- **Condition**: **ONLY** if N ≥ 10 AND number of distinct tracts (k) ≥ 2.
- **Resolution of T022**: The spec (FR-005) mandates Bonferroni. The plan implements Bonferroni but includes a mandatory **Limitations Note** in the output report stating: "Bonferroni correction was applied despite known non-independence of brain tracts, which may result in conservative Type II errors. Robust Variance Estimation (RVE) is a preferred alternative for correlated data but was not implemented per spec requirement FR-005."

### 5. Qualitative Extraction (T013)
- **Decision**: Use regex and keyword matching on abstract text.
- **Logic**:
 - **Tract Detection**: Regex for `[A-Za-z]+\s+(fasciculus|bundle|tract|pathway)` (e.g., "arcuate fasciculus").
 - **Directional Detection**: Regex for `(increased|decreased|reduced|enhanced|correlated)\s+(FA|MD|FA/MD)` in proximity to tract names.
 - **Extraction**: Store the full sentence or clause as `qualitative_desc`.
 - **Validation**: If `r` or `n` are not found in the abstract, the study is marked as "narrative candidate" and excluded from the quantitative pool.

### 6. Fallback Protocol (FR-006)
- **Decision**: If unique (Author, Year) pairs < 10, switch to narrative mode.
- **Output**: Generate a structured text summary of qualitative findings instead of a pooled effect size.

### 7. Narrative Synthesis Methodology
- **Decision**: Use a thematic analysis framework for the narrative review.
- **Coding Scheme**:
 - **Theme 1**: Tract Involvement (e.g., "Arcuate Fasciculus is most frequently cited").
 - **Theme 2**: Metric Direction (e.g., "FA increases associated with preference").
 - **Theme 3**: Population Differences (e.g., "Musicians vs. Non-musicians").
- **Output**: A structured summary report organized by these themes.

## Compute Feasibility

- **Memory**: The analysis is lightweight (pandas dataframes, statsmodels). Expected peak RAM < 1GB.
- **CPU**: No GPU required. `statsmodels` and `scipy` run efficiently on 2 vCPU.
- **Time**: Processing multiple studies takes seconds. The 15-minute limit (SC-001) is generous.
- **Disk**: Input CSVs and output PNGs are small (<10MB total).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No studies found with direct (r, n) pairs | High | Trigger narrative fallback (FR-006). Use synthetic data for testing. |
| I² calculation fails to converge | Medium | Log error, fall back to fixed-effects model (as per Edge Cases). |
| Egger's test requires N≥10 but N=9 | Low | Skip test, report specific reason (T021). |
| PNG files exceed 5MB | Medium | Optimize DPI and compression in `matplotlib` (T031). |
| Heterogeneity too high (I² > 75%) | High | Suppress pooled estimate in report; emphasize narrative findings. |
