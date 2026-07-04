# Research: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## Overview

This research document outlines the data strategy, dataset verification, and methodological approach for investigating the correlation between gut microbiome composition and sleep quality. It adheres to the project constitution's requirement for verified accuracy and data hygiene.

**CRITICAL FINDING**: The project is **BLOCKED** because the provided "# Verified datasets" block contains **NO** dataset that includes both 16S rRNA OTU data AND sleep quality metrics (efficiency, duration). The American Gut Project (AGP) is assumed in the spec, but no verified URL for AGP with sleep metadata exists in the provided list.

## Dataset Strategy

### Primary Data Source: American Gut Project (AGP)

The American Gut Project is the primary source for 16S rRNA OTU count tables and associated metadata. It is a large-scale, citizen-science project that provides open access to gut microbiome data from thousands of participants.

**Verification Status**: The AGP dataset is a well-known public resource. However, the specific URL for the pre-processed OTU tables and sleep metadata must be confirmed against the "# Verified datasets" block provided in the prompt.

**Constraint Check**: The prompt's "# Verified datasets" block does **not** list a verified URL for the American Gut Project or any dataset containing specific "sleep efficiency" or "sleep duration" variables linked to 16S rRNA data. The listed datasets are:
- `turkishloyd` (OTU parquet) - No sleep metadata.
- `kali-ai/otus` (OTU json) - No sleep metadata.
- `karan451/BMI-labeled-faced` (BMI csv) - No microbiome or sleep data.
- `NurlanAliyevofficial/Brain-tumor...` (BMI csv) - **Invalid URL (HTTP 404)**. This dataset is unreachable and cannot be used.
- `minhthong/flashdeal_data_BMI_historical_signal` (BMI parquet) - No microbiome or sleep data.
- `AdityaMayukhSom/MixSub-LLaMA-3.2...` (CPU-only parquet) - No microbiome or sleep data.

**Critical Finding**: **No verified dataset in the provided list contains both 16S rRNA OTU data AND sleep quality metrics (efficiency, duration).** The spec assumes the existence of such a dataset in the American Gut Project, but the "Verified datasets" block provided for this planning phase does not contain a valid, reachable URL for it.

**Action Plan**:
1.  **Primary Attempt**: The ingestion script will attempt to fetch the AGP data from the canonical public repository (as per FR-001). If the specific URL is not provided in the "Verified datasets" block, the script will fail gracefully with a clear error message indicating that the required dataset (AGP with sleep metadata) is not available in the verified list.
2.  **Fallback**: If the AGP data is unavailable, the pipeline will halt. The spec's assumption that "The American Gut Project public repository contains... self-reported sleep questions" cannot be validated against the provided verified sources.
3.  **Dataset Substitution**: No substitution is possible with the provided verified datasets, as none contain the necessary combination of variables (OTU counts + sleep metrics). Using a dataset with only BMI or only OTUs would violate the research question.

**Decision**: The plan proceeds with the assumption that the AGP data will be fetched from its canonical source (as per FR-001), but the `research.md` explicitly flags the **lack of a verified URL** in the provided list. If the canonical source is unreachable or lacks the specific sleep variables, the study cannot proceed as specified. The project is currently **BLOCKED** until a verified source is identified.

### Variable Mapping

| Variable | Source Field | Description | Availability Status |
|----------|--------------|-------------|---------------------|
| `sleep_efficiency` | `sleep_efficiency` | Self-reported sleep efficiency (%) | **MISSING** in all verified sources |
| `sleep_duration_hours` | `sleep_duration_hours` | Self-reported sleep duration (hours) | **MISSING** in all verified sources |
| `antibiotic_use_last_3m` | `antibiotic_use_last_3m` | Antibiotic use in last 3 months (True/False) | **MISSING** in all verified sources |
| `shannon_diversity` | Computed | Shannon index of alpha-diversity | N/A (requires OTU data) |
| `simpson_diversity` | Computed | Simpson index of alpha-diversity | N/A (requires OTU data) |
| `observed_otus` | Computed | Observed OTUs count | N/A (requires OTU data) |
| `age` | `age` | Participant age | **MISSING** in all verified sources |
| `bmi` | `bmi` | Body Mass Index | Present in some, but no OTU data |

**Note**: If the actual AGP dataset uses different field names, the ingestion script must include a mapping step. However, the primary issue is the **absence of the dataset itself** in the verified list.

## Methodological Approach

### Data Preprocessing

1.  **Download**: Fetch OTU tables and metadata from the AGP repository. **If the dataset is not found in the verified list, the pipeline halts.**
2.  **Filter**:
    - Exclude samples where `antibiotic_use_last_3m` is True.
    - Exclude samples where `sleep_efficiency` or `sleep_duration_hours` are missing.
    - Exclude samples with missing `age` or `bmi` for multivariate analysis (optional, per edge cases).
3.  **Compute Diversity**: Calculate Shannon, Simpson, and Observed OTUs indices from the OTU count tables using `scikit-bio`. **A rarefaction step is mandatory to normalize sequencing depth before computing diversity indices to prevent artifacts.**

### Statistical Analysis

1.  **Correlation**: Perform Spearman rank correlation between each diversity index (Shannon, Simpson, Observed OTUs) and each sleep metric (efficiency, duration).
2.  **Multiple Comparison Correction**: Apply Benjamini-Hochberg (BH) correction to the raw p-values to control the False Discovery Rate (FDR).
3.  **Significance Threshold**: Flag correlations with adjusted p-value (q-value) < 0.05 as significant.
4.  **Effect Size**: Report correlations with |r| > 0.3 as "moderate" (per FR-004).

### Visualization

1.  **Scatterplots**: Generate scatterplots with regression lines for significant correlations.
2.  **Boxplots**: Generate boxplots of diversity indices grouped by sleep efficiency quartiles (Q1-Q4).

## Assumptions & Limitations

- **Observational Nature**: The study is observational; no causal claims will be made.
- **Data Availability**: **The study is currently BLOCKED.** The success of the pipeline depends on the availability of the AGP dataset with the required sleep metadata. If the dataset is unavailable or lacks the necessary variables (as confirmed by the verified sources), the study cannot be completed as specified.
- **Power**: The statistical power depends on the final sample size after filtering. If the filtered dataset is too small, the study may be underpowered to detect moderate correlations.
- **Collinearity**: Diversity indices are inherently correlated. The analysis will report them descriptively without claiming independent effects.
- **Sequencing Depth**: Without a rarefaction step, diversity indices may be biased by sequencing depth. The plan includes this step to ensure methodological soundness.

## Ethical Considerations

- **Privacy**: The AGP dataset is public and anonymized. No personally identifiable information (PII) will be handled.
- **Data Usage**: The data will be used strictly for the purposes outlined in the AGP's terms of service.

## Conclusion

This research plan outlines a rigorous approach to investigating the gut-sleep axis. However, it explicitly identifies a **critical gap**: the provided "# Verified datasets" block does not contain a valid, reachable URL for the American Gut Project dataset with sleep metadata. The pipeline will attempt to fetch from the canonical source, but if that fails or the variables are missing, the study will halt with a clear error. **No alternative dataset from the verified list can substitute for the required data.** The project is currently **BLOCKED** until a verified source is identified.