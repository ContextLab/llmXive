# Feature Specification: Evaluating Statistical Fidelity of Synthetic Data

**Feature Branch**: `001-statistical-fidelity`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Statistical Properties of Synthetic Data Generation Techniques"

## User Scenarios & Testing

### User Story 1 - Automated Fidelity Pipeline Execution (Priority: P1)

The system MUST execute a complete end-to-end pipeline on a CPU-only environment that downloads public tabular benchmarks, trains three distinct generative models (CTGAN, DP‑GAN, CopulaGAN) with constrained resources, generates synthetic datasets, and computes statistical descriptors without requiring manual intervention or GPU acceleration.

**Why this priority**: This is the foundational capability. Without a working, reproducible pipeline that respects the free‑tier compute constraints (CPU‑only, ≤7 GB RAM), no statistical comparison can occur. It delivers the raw data required for all subsequent analysis.

**Independent Test**: The system can be fully tested by running the `run_fidelity.py` script on a GitHub Actions free‑tier runner and verifying that it exits with code 0, produces synthetic CSV files, and outputs a JSON report of statistical metrics within 6 hours.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions free‑tier runner (2 CPU, 7 GB RAM, no GPU), **When** the pipeline script is executed with default public datasets (e.g., UCI Adult), **Then** the system must complete training for all three models and generate synthetic data within 360 minutes, consuming no more than 7 GB of RAM at any peak.
2. **Given** a dataset with missing values, **When** the preprocessing step is executed, **Then** the system must impute missing values and encode categoricals such that the resulting training matrix has no nulls and is ready for model ingestion.
3. **Given** the training constraints (≤30 epochs) and optional early‑stopping criteria, **When** the models are trained, **Then** the system must terminate training exactly at epoch 30 **or** earlier if early‑stopping criteria are met, preventing memory overflow.

---

### User Story 2 - Statistical Metric Computation and Comparison (Priority: P2)

The system MUST compute and compare specific statistical metrics (means, variances, marginal PDFs, pairwise correlations) between real and synthetic datasets, applying appropriate goodness‑of‑fit tests (KS‑test, Chi‑square, permutation‑based correlation test) to quantify the divergence.

**Why this priority**: This is the core research value. It transforms raw generated data into quantifiable evidence of fidelity, directly addressing the research question regarding the preservation of statistical fabric.

**Independent Test**: The system can be tested by running the metric computation module on a static pair of real/synthetic datasets and verifying that the output contains valid p‑values for KS‑tests, permutation‑based correlation test statistics, and effect‑size measures that match manual calculations on a subset of columns.

**Acceptance Scenarios**:

1. **Given** a real dataset and its synthetic counterpart, **When** the marginal distribution analysis runs, **Then** the system must output a Kolmogorov‑Smirnov statistic and p‑value for every continuous column, a Chi‑square statistic for every categorical column, **and** kernel‑density‑estimate (KDE) marginal PDFs visualized side‑by‑side with the empirical histograms.
2. **Given** the correlation matrices of real and synthetic data, **When** the correlation comparison runs, **Then** the system must calculate the absolute difference in Pearson and Spearman coefficients for all column pairs and flag any pair where the permutation‑based test indicates a significant difference (p < 0.05 after correction).
3. **Given** the computed metrics, **When** the aggregation step runs, **Then** the system must produce a summary table showing the mean and standard deviation of metric differences across all evaluated datasets and methods, and a paired‑test (t‑test or Wilcoxon) assessing whether any method outperforms the others overall.

---

### User Story 3 - Methodologically Defensible Reporting (Priority: P3)

The system MUST generate a final report that includes sensitivity analyses for decision thresholds, corrects for multiple comparisons, and explicitly frames findings as associational to ensure methodological soundness and reproducibility.

**Why this priority**: This ensures the research output is scientifically valid and defensible against peer review, addressing the panel's requirements for inference framing, multiplicity, and threshold justification.

**Independent Test**: The system can be tested by inspecting the final report artifacts to confirm the presence of a sensitivity analysis section, a multiple‑comparison correction note, and explicit language framing results as "associational" rather than "causal."

**Acceptance Scenarios**:

1. **Given** a set of hypothesis tests performed across multiple metrics, **When** the reporting module generates the summary, **Then** the system must apply a Benjamini‑Hochberg correction to the p‑values and report the corrected significance status.
2. **Given** a decision threshold for "acceptable fidelity" (e.g., p‑value cutoff), **When** the sensitivity analysis runs, **Then** the system must re‑evaluate the headline faithful/unfaithful classification at thresholds {0.01, 0.05, 0.1} and report how the fraction of columns classified as faithful changes.
3. **Given** the observational nature of the study (no random assignment), **When** the conclusion section is drafted, **Then** the text MUST explicitly state that findings describe "associations" and "distributions" and MUST NOT claim causal effects of the generators on the data properties.

### Edge Cases

- What happens when a specific dataset (e.g., Higgs) exceeds the 7 GB RAM limit during one‑hot encoding of high‑cardinality categoricals? **System must** sample rows uniformly to reduce size **or** drop the high‑cardinality columns, logging the action (see FR‑009).
- How does the system handle a generator (e.g., DP‑GAN) that fails to converge within the 30‑epoch limit on a specific dataset? **System must** log the failure, record `NaN` for all metrics of that model‑dataset pair, and continue processing the remaining models/datasets (see FR‑010).
- What happens if the synthetic data generator produces a dataset with zero variance in a column that had variance in the real data? **System must** flag this column as a total fidelity failure without crashing the KS‑test (see FR‑011).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and preprocess at least three public tabular datasets (e.g., UCI Adult, Credit Card Fraud, Covertype, **Higgs**) via direct URLs, handling missing values, encoding categoricals, and performing an 80/20 train‑hold‑out split after preprocessing. (See US‑1)
- **FR-002**: System MUST train CTGAN, DP‑GAN, and CopulaGAN models using the `sdv` library with a maximum of 30 epochs, **optional early‑stopping based on validation loss**, and default hyperparameters **except** that DP‑GAN must be configured with a privacy budget ε = 1.0 (logged). No GPU usage is permitted. (See US‑1)
- **FR-003**: System MUST generate synthetic datasets with a row count matching the **training** set for each method and dataset combination. (See US‑1)
- **FR-004**: System MUST compute marginal distribution statistics (mean, variance, KS‑statistic, Chi‑square statistic, KDE PDFs) and pairwise correlation matrices (Pearson, Spearman) for both real **hold‑out** and synthetic data. (See US‑2)
- **FR-005**: System MUST apply statistical significance tests (Kolmogorov‑Smirnov, Chi‑square, **permutation‑based correlation test**) to compare real vs. synthetic metrics and record both p‑values **and** effect sizes. (See US‑2)
- **FR-006**: System MUST perform a multiple‑comparison correction (Benjamini‑Hochberg) on the collection of p‑values generated across all metrics and datasets. (See US‑3)
- **FR-007**: System MUST execute a sensitivity analysis sweeping the significance threshold over {0.01, 0.05, 0.1} and report the variation in **faithful/unfaithful classification** stability, using the **control‑perturbation dataset** defined in FR‑022 as the ground‑truth reference for false‑positive/false‑negative rates. (See US‑3)
- **FR-008**: System MUST output a final report that explicitly frames all findings as associational and includes a sensitivity analysis table. (See US‑3)
- **FR-009**: System MUST detect when RAM usage exceeds 7 GB during preprocessing or training; upon detection it must either down‑sample the dataset uniformly or drop high‑cardinality columns, and must log the mitigation action. (See US‑1, Edge Cases)
- **FR-010**: System MUST detect non‑convergence of any generator within the epoch limit, log the failure, record `NaN` for all associated metrics, and continue processing remaining models/datasets. (See US‑1, Edge Cases)
- **FR-011**: System MUST detect any synthetic column with zero variance when the corresponding real column has non‑zero variance, flag the column as a fidelity failure, and gracefully skip the KS‑test for that column. (See US‑2, Edge Cases)
- **FR-012**: System MUST aggregate per‑dataset metric differences into a summary table reporting the mean and standard deviation of each metric across all evaluated datasets and methods. (See US‑2, Acceptance Scenario 3)
- **FR-013**: System MUST support early‑stopping during model training based on validation loss improvement of less than 0.001 over three consecutive epochs. (See US‑1, Scenario 3)
- **FR-014**: System MUST compute kernel‑density‑estimate marginal PDFs for continuous columns and generate side‑by‑side histograms, QQ‑plots, and correlation heatmaps as visual artifacts for each dataset‑method pair. (See US‑2)
- **FR-015**: System MUST split each preprocessed dataset into an [deferred] training set (used for model fitting) and a [deferred] hold‑out set (used exclusively for fidelity evaluation). (See US‑2)
- **FR-016**: System MUST log the privacy‑budget ε used for DP‑GAN training and expose it in the final report. (See US‑1)
- **FR-017**: System MUST run each (model, dataset) combination with three distinct random seeds and aggregate metric results across seeds (mean ± standard deviation). (See US‑2)
- **FR-018**: System MUST perform paired significance testing (paired t‑test or Wilcoxon signed‑rank when non‑normal) on metric differences between methods to assess overall superiority of any method. (See US‑2)
- **FR-019**: System MUST generate a random‑noise baseline dataset by sampling each column independently from the empirical marginal distribution of the **hold‑out** set using a fixed seed (seed = 42). This baseline is used for SC‑003 comparisons. (See SC‑003)
- **FR-020**: System MUST classify a column as “faithful” only if **both** (i) the corrected p‑value ≥ 0.05 **and** (ii) the effect‑size metric is below a community‑standard threshold (KS ≤ 0.1 for continuous, χ² ≤ χ²₀.₉₅ for categorical). Otherwise the column is “unfaithful”. (See SC‑002)
- **FR-021**: System MUST create a **control‑perturbation dataset** by taking the real hold‑out set, randomly permuting [deferred] of rows in each column, and using this as the ground‑truth reference for computing false‑positive and false‑negative rates in the sensitivity analysis. (See FR‑007)
- **FR-022**: System MUST report false‑positive and false‑negative rates for the faithful/unfaithful classification at each threshold in the sensitivity analysis, using the control‑perturbation dataset (FR‑021) as the truth set.

### Key Entities

- **Dataset**: A tabular data source containing real observations, characterized by a set of numeric and categorical columns.
- **SyntheticDataset**: A generated tabular dataset produced by a specific model (CTGAN, DP‑GAN, or CopulaGAN) intended to mimic the statistical properties of a specific Dataset.
- **FidelityMetric**: A quantitative value (e.g., KS‑statistic, correlation difference, effect size) measuring the divergence between a real Dataset and a SyntheticDataset.
- **StatisticalTestResult**: The output of a hypothesis test (p‑value, statistic, effect size) comparing a FidelityMetric against a null hypothesis of no difference.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The fraction of datasets for which the pipeline completes without memory overflow (≤7 GB RAM) is measured against the total number of datasets selected. (See FR‑001)
- **SC-002**: The number of columns where the synthetic data marginal distribution is statistically indistinguishable from the real hold‑out **and** meets the effect‑size threshold (see FR‑020) is measured against the total number of columns tested. (See FR‑005, FR‑020)
- **SC-003**: The magnitude of correlation distortion (mean absolute difference in Pearson/Spearman coefficients) is measured against the random‑noise baseline generated by FR‑019. (See FR‑019, FR‑018)
- **SC-004**: The stability of the faithful/unfaithful classification is measured as the proportion of column‑method pairs whose classification changes across the three thresholds {0.01, 0.05, 0.1}. (See FR‑007, FR‑022)
- **SC-005**: The computational time for the full pipeline (download, train, generate, analyze) is measured against an established wall‑clock time limit. (See FR‑001)

## Assumptions

- The `sdv` Python library and its dependencies (including `ctgan`, `sdv`, `pandas`, `numpy`, `scipy`, `scikit-learn`) can be installed and run within the 14 GB disk space limit of the free‑tier runner.
- The selected public datasets (UCI Adult, Credit Card Fraud, Covertype, **Higgs**) are available via direct HTTP links and do not require interactive login or complex scraping logic.
- A modest training‑epoch limit (with optional early‑stopping) is sufficient to produce a synthetic dataset with discernible statistical properties for comparison., even if not fully converged.
- The "associational" framing is sufficient for the research goal; no causal claims regarding privacy guarantees or generator efficacy are being made, only statistical fidelity.
- The `sdv` library's default implementations of CTGAN, DP‑GAN, and CopulaGAN do not require CUDA or GPU acceleration to function, even if performance is slower than on GPU.
- The sample sizes in the public datasets are large enough that the power of the KS‑test and permutation‑based correlation tests is adequate to detect meaningful deviations without requiring a formal power analysis (power is assumed sufficient due to large N in UCI datasets).
- The train/hold‑out split (80/20) provides an unbiased evaluation set, mitigating over‑fitting concerns.
- DP‑GAN is trained with a privacy budget ε = 1.0 by default; this value is logged for transparency.
- Random‑seed replication (three seeds) yields robust estimates of metric variability.
