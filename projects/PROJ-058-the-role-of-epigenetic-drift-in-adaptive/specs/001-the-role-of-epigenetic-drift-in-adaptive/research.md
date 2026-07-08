# Research: The Role of Epigenetic Drift in Adaptive Landscape Exploration

## 1. Problem Statement & Hypothesis

**Research Question**: How does multi-generational epigenetic variance correlate with gene expression variability in model organisms exposed to fluctuating environmental conditions?

**Hypotheses**:
- **Null (H0)**: No association exists between epigenetic drift and expression variability.
- **Alternative (H1)**: There is a statistically significant **association** between epigenetic variance and expression variability in fluctuating environments.
 - **CRITICAL CAVEAT**: This study is **observational**. The analysis **cannot establish causality** (i.e., it cannot prove drift *drives* expression changes). Claims will be framed strictly as "associational strength" to avoid construct validity failure.

**Context**: As noted by reviewer `freeman-dyson-simulated`, this project aims to be "Birds of the genome," exploring the topological freedom of the adaptive landscape beyond genetics. The study investigates whether epigenetic variance acts as "noise" or a "mechanism for rapid adaptation."

## 2. Dataset Strategy

The project relies on **verified datasets** from the provided list. The spec requires matched multi-generational datasets (methylation + RNA-seq) for mouse, C. elegans, or Drosophila.

### Verified Sources
The following URLs are the **only** sources cited for data acquisition. **If a specific biological dataset (e.g., "Mouse Multi-Gen Methylation") is not present in these verified sources, the project will explicitly report the unavailability rather than fabricating a URL.**

| Dataset Type | Verified Source URL | Notes |
|:--- |:--- |:--- |
| **GEO (Metadata)** | ` | Primary source for GEO metadata. **Likely lacks specific "multi-generational" + "fluctuating" + "matched methylation/RNA-seq" tags.** |
| **RNA-seq (Index)** | ` | Contains RNA-seq indices. **Does not inherently contain methylation data or specific "fluctuating environment" metadata.** |
| **RNA-seq (Processed)** | ` | Candidate for expression data. **Does not contain matched methylation data.** |

**Note**: The URLs listed for "drug_reviews", "yelp_reviews", "CelebA", and "pandaset" in the initial draft have been **removed** as they are irrelevant to biological omics.

### Dataset Feasibility Analysis
**Critical Gap Identification**:
The spec requires **matched** multi-generational datasets containing **both** methylation and RNA-seq under **fluctuating environmental conditions**.
- The verified GEO/ENCODE URLs provided appear to be general repositories or specific non-biological datasets.
- The `recount3` and `Paul` RNA-seq datasets do not inherently contain methylation data or specific "fluctuating environment" metadata in their filenames.
- **Decision**: The `discovery` phase (FR-000) will attempt to query the `Geo170K` parquet file for multi-generational methylation/RNA-seq matches. **If the verified sources do not contain the specific matched multi-generational datasets required (≥3), the pipeline will halt with a "Data Unavailable" status (US-0, Acceptance Scenario 2).**
- **No Fabrication**: We will **not** invent a URL for a "Mouse Multi-Gen" dataset if it is not in the verified list. The project will explicitly state: "Verified sources do not contain ≥3 matched multi-generational datasets with fluctuating metadata."

### Data Loading Strategy
- **GEO/ENCODE**: Load via `pandas.read_parquet` or `pandas.read_json` from the verified HuggingFace URLs.
- **RNA-seq**: Load via `pandas.read_csv` or `pandas.read_json` from verified sources.
- **Filtering**: Apply strict filters for organism (mouse, C. elegans, Drosophila), condition (fluctuating), and data type (methylation + RNA-seq). **If no matches are found, the pipeline halts.**

## 3. Methodology

### 3.1 Data Preprocessing (FR-001, FR-002)
1. **RNA-seq Normalization**:
 - Apply **DESeq2-like variance stabilization** (using `scipy.stats` or `sklearn` approximations) to raw counts.
 - *Constraint*: DESeq2 is a Bioconductor R package. The plan will use a Python equivalent (e.g., `variance_stabilizing_transformation` from `scipy` or a simplified log-normalization with size factors) to run on CPU without R dependencies, as per compute feasibility.
 - **Stratification**: Attempt to group data by specific **stressor type** (e.g., temperature, nutrient, chemical) if metadata permits.
2. **Methylation Normalization**:
 - Apply **CpG-density normalization** to account for probe density variations.
 - Filter out samples with global methylation <1%.
 - **Stratification**: Group by stressor type.
3. **Leave-One-Generation-Out (LOGO) Jackknife**:
 - To break circular validation, variance is calculated on **disjoint subsets** of generations.
 - **Method**: For a dataset with generations $G_1, G_2, G_3, \dots$:
 - Calculate **Epigenetic Variance** using odd generations ($G_1, G_3, \dots$).
 - Calculate **Expression Variance** using even generations ($G_2, G_4, \dots$).
 - This ensures the predictor and outcome are not derived from the exact same sample set, addressing the "noisy genes are noisy in both layers" tautology.
 - **Uncertainty**: With N<10, variance estimates are unstable. The plan will report **uncertainty intervals** (via bootstrapping the variance estimator itself) rather than relying solely on a point estimate.

### 3.2 Correlation Analysis (FR-003, FR-004)
1. **Primary Metric**: Spearman's rank correlation coefficient ($\rho$) between **LOGO-derived** epigenetic variance and **LOGO-derived** expression variance.
 - *Justification*: Robust to outliers and non-linear relationships. **Associational only.**
2. **Stratification**:
 - Calculate $\rho$ for "fluctuating" condition subset.
 - Calculate $\rho$ for "constant" condition subset (if available).
 - **Stressor Stratification**: Calculate $\rho$ separately for distinct stressor types (e.g., temperature vs. nutrient) to control for confounding.
3. **Significance Testing**:
 - **Permutation Test**: 10,000 iterations to generate an empirical p-value.
 - Compare empirical p-value against theoretical p-value (SC-002).
 - **Statistical Rigor**: Acknowledgement that observational data implies **associational claims**, not causal. **If N<10, the correlation is treated as a heuristic with massive uncertainty.**

### 3.3 Robustness & Sensitivity (FR-005, SC-003)
1. **Threshold Sweep**: Vary minimum generation threshold $\in \{3, 4, 5\}$.
2. **Stability Check**: Report $\Delta\rho$ across thresholds. Flag if $|\Delta\rho| > 0.1$.
3. **Zero Variance Handling**: Explicitly exclude genes with zero variance in both layers to avoid division by zero (Edge Case).
4. **Temporal Resolution Flag**: If a dataset lacks sufficient granularity (N<3 generations or missing timescale), the `CorrelationResult` includes `temporal_resolution_flag: "insufficient"` and the result is excluded from the final association claim.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions Free Tier (2 CPU, **2GB RAM**).
- **Memory**: Data subset to ~2GB RAM limit. Processing done in chunks if necessary.
- **Time**: 10,000 permutation iterations for ≤5,000 genes is feasible on 2 CPU cores within 6 hours.
- **Libraries**: `pandas`, `numpy`, `scipy`, `scikit-learn` (CPU wheels only). No GPU/CUDA.
- **Risk**: If the verified datasets are large (e.g., full transcriptome > 50k genes), sampling or gene filtering will be applied to ensure runtime < 6h.

## 5. Statistical Rigor & Limitations

- **Multiple Comparisons**: If multiple genes or conditions are tested, a correction (e.g., Benjamini-Hochberg) will be considered if the number of tests exceeds a threshold, though the primary focus is the aggregate correlation.
- **Causal Inference**: Claims will be framed as **associational**. The study is observational; no randomization of environmental conditions is performed by the pipeline (data is pre-existing).
- **Measurement Validity**: Relies on the quality of the public GEO/ENCODE metadata. If metadata is missing (e.g., "fluctuation timescale"), the dataset is flagged (US-1, SC-3).
- **Collinearity**: Acknowledgement that if predictors are derived from the same assay, collinearity is high. Here, methylation and RNA-seq are independent assays, reducing mechanical artifacts. **The LOGO jackknife further reduces sample-induced collinearity.**
- **Low-N Instability**: With N<10 generations, variance estimates are highly unstable. The plan explicitly reports this limitation and treats the correlation as a heuristic association with wide uncertainty bounds.

## 6. Decision Rationale

- **Why LOGO Jackknife?**: To break the circular validation where variance of Layer A and Layer B are derived from the same N samples. Simple bootstrap on the same N does not create independence.
- **Why Spearman?**: Robust to outliers and non-linear relationships common in biological variance data.
- **Why Permutation?**: Theoretical p-values assume normality, which variance distributions often violate. Permutation provides a distribution-free empirical test.
- **Why CPU-only?**: Required by the deployment environment (GitHub Actions Free Tier). Deep learning models are unnecessary for correlation analysis and would violate compute constraints.
- **Why Strict Dataset Filtering?**: To ensure "Data Hygiene" (Constitution Principle III) and "Multi-Omic Data Integrity" (Principle VI).
