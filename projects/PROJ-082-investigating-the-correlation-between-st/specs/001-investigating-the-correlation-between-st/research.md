# Research: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Executive Summary

This research phase evaluates the feasibility of conducting a meta-analysis on the relationship between structural brain connectivity (specifically white matter integrity via dMRI) and music preferences. The primary challenge identified is the scarcity of direct empirical studies reporting correlation coefficients (`r`) between specific dMRI tracts and quantitative music preference scores.

The **Dataset Strategy** confirms that while verified datasets exist for PubMed literature and general MRI metadata, **no single verified dataset contains the specific (tract, r, n) tuples required for direct meta-analysis**. Therefore, the implementation plan assumes a "Literature Extraction" workflow where the system parses a pre-defined CSV of extracted studies (simulating the output of a manual literature search) rather than scraping raw text from the verified PubMed JSONL files directly for effect sizes. The verified datasets serve as the *source of the literature list* (titles/abstracts) to validate the existence of relevant studies, but the *effect size data* must be manually curated or simulated for the pipeline to function as a meta-analysis engine.

## Dataset Strategy

| Dataset Name | Verified URL | Relevance to Analysis | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **PubMed** | ` | Source of literature titles/abstracts to identify potential studies. | **Read-Only Reference**: Used to validate that studies exist in the literature. Effect sizes (`r`, `n`) are **NOT** extracted directly from this file due to format (abstracts lack statistical tables). The pipeline will expect a curated CSV input for statistical synthesis. |
| **Brain_MRI_Dataset** | ` | General MRI metadata. | **Read-Only Reference**: Contains image metadata but no behavioral preference data. Not suitable for direct correlation analysis. |
| **FOMO45K** | ` | Large-scale MRI mapping. | **Read-Only Reference**: No behavioral preference data. |
| **SKIP_NoClip_Data** | ` | Unrelated to neuroscience/music. | **Excluded**: Irrelevant to the research question. |

**Critical Finding**: None of the verified datasets contain the specific combination of (dMRI tract metrics, sample size, music preference score) required for the meta-analysis.
* **Decision**: The `code/` pipeline will be designed to ingest a **curated CSV** (e.g., `data/raw/studies_extracted.csv`) representing the output of a manual literature review. The `research.md` documents that the "Literature Search" step is a prerequisite manual task or a separate NLP extraction module (not part of this statistical pipeline) to populate this CSV.
* **Fallback**: If the curated CSV contains fewer than 10 unique (Author, Year) pairs, the pipeline will automatically trigger the **Narrative Synthesis** mode (as per FR-006 and Principle VII).

## Statistical Methodology

### Meta-Analysis Model
- **Model**: Random-Effects Model (DerSimonian-Laird or Restricted Maximum Likelihood via `statsmodels`).
- **Effect Size**: Pearson correlation coefficient (`r`).
- **Transformation**: Fisher's `z` transformation will be applied to `r` before aggregation to normalize the distribution, then back-transformed for reporting.
- **Heterogeneity**: Quantified using $I^2$ statistic.
- **Publication Bias**: Assessed via Egger's linear regression test (conditional on $N \ge 10$).

### Multiple Comparison Correction
- **Method**: Bonferroni correction.
- **Trigger**: Applied only if $N \ge 10$ AND number of distinct tracts $k \ge 2$.
- **Correction Factor**: $\alpha_{adj} = \alpha / k$.
- **Non-Independence**: If multiple tracts from the same study are included, they are treated as distinct comparisons for Bonferroni correction **only if** the study reports them as independent analyses. Otherwise, the study is treated as a single unit for the primary aggregation, with a note on the potential for within-study correlation.

### Power Analysis
- **Trigger**: Always performed.
- **Logic**: If $N < 20$ and the expected effect size is small (r < 0.3), a `power_warning` is included in the output. This is distinct from the $N < 10$ Egger's test gate.

### Narrative Synthesis Fallback
- **Trigger**: $N < 10$ unique studies.
- **Output**: Structured text summary describing the directionality and consistency of findings across the available studies, without pooled effect sizes.

## Tract Harmonization
To address the variability in tract definitions across studies (e.g., "Arcuate Fasciculus" vs "AF"), the pipeline will map all `tract_name` strings to a standard ontology (e.g., JHU White Matter Tractography Atlas). Studies using non-standard names will be flagged, and their data will be aggregated only if a clear mapping can be established. This ensures the construct validity of the pooled effect size.

## Data Provenance & Validation
- **Input Data**: The pipeline expects `data/raw/studies_extracted.csv` as a **user-provided artifact**. This file represents the output of a manual literature review. The pipeline does **not** attempt to scrape or auto-extract effect sizes from raw literature (PubMed abstracts) because they lack statistical tables.
- **Unit Testing**: Synthetic data is used **only** to verify the mathematical correctness of the statistical engines (e.g., "Does the code correctly calculate I²?"). These tests do not validate the scientific claim, only the code logic.
- **Scientific Execution**: When run with manually curated data, the pipeline generates empirical findings. The validity of these findings depends on the quality of the manual curation, which is outside the scope of the code but documented in the `research.md`.

## Feasibility Assessment (Compute)
- **Memory**: The analysis of < 100 studies requires negligible RAM (< 500MB).
- **CPU**: Statistical calculations (I², Egger's) are $O(N)$ and will complete in seconds.
- **Time**: Total runtime on GitHub Actions (2 vCPU) estimated at < 5 minutes.
- **Constraints**: No GPU required. All libraries (`statsmodels`, `scipy`) have CPU wheels available.

## Risks & Mitigations
- **Risk**: Insufficient studies ($N < 10$) for quantitative analysis.
 - **Mitigation**: The pipeline is explicitly designed to detect this and switch to Narrative Mode (FR-006). This is an acceptable outcome per the spec.
- **Risk**: Missing effect sizes (only p-values reported).
 - **Mitigation**: The extraction module will attempt conversion using standard formulas (p-value to z-score to r) or flag the study for exclusion with a log entry.
- **Risk**: Model convergence failure.
 - **Mitigation**: Fallback to Fixed-Effects model if Random-Effects fails to converge, with a warning log.
- **Risk**: Tract definition heterogeneity.
 - **Mitigation**: Mapping to a standard ontology and flagging non-standard entries.