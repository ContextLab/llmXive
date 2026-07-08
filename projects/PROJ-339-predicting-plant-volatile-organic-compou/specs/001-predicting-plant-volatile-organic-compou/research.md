# Research: Predicting Plant VOC Emission Profiles from Genomic and Environmental Data

## Problem Statement

The goal is to predict Volatile Organic Compound (VOC) emission profiles in *Arabidopsis thaliana* using genomic (RNA-seq) and environmental data. This requires integrating heterogeneous data sources, handling missing values, and building a predictive model that identifies key genomic drivers (e.g., terpene synthases) while maintaining statistical rigor.

**Critical Scope Limitation**: Due to the absence of verified paired *Arabidopsis* RNA-seq/VOC datasets in public repositories, this project is currently scoped as a **Methodological Simulation & Pipeline Validation** study. The primary objective is to validate the pipeline logic (ingestion, normalization, modeling, interpretation) on synthetic data. Real biological discovery is deferred until verified paired data is acquired.

## Dataset Strategy

### Verified Sources Analysis

The project relies on the following verified dataset sources. **Critical Note**: None of the provided verified URLs contain *Arabidopsis thaliana* paired RNA-seq and VOC data.

| Category | Verified URL(s) | Relevance to Project | Status |
|:--- |:--- |:--- |:--- |
| **RNA-seq** | ` | Human (GTEx) data. | **Not Applicable** |
| | ` | Unspecified species (likely human/mouse). | **Not Applicable** |
| | ` | Unspecified species. | **Not Applicable** |
| **VOC** | ` | Computer Vision (Pascal VOC images). | **Not Applicable** |
| | ` | Computer Vision. | **Not Applicable** |
| | ` | Audio/Emotion. | **Not Applicable** |
| **NCBI/GEO** | ` | Disease ontology, not plant RNA-seq. | **Not Applicable** |
| | ` | Human GEO data. | **Not Applicable** |
| | ` | Geometry/Visualization. | **Not Applicable** |
| | ` | Reasoning on GEO data. | **Not Applicable** |
| **TPM** | ` | Emotion data. | **Not Applicable** |
| | ` | Pangenome (likely human). | **Not Applicable** |
| | ` | Question Answering. | **Not Applicable** |
| **Other** | ` | Medical imaging. | **Not Applicable** |
| | ` | LLM evaluation. | **Not Applicable** |
| **Plant VOC** | **NO verified source found** | *Arabidopsis* VOC data required. | **BLOCKING GAP** |
| **CO2** | **NO verified source found** | Environmental metadata required. | **BLOCKING GAP** |

### Data Gap Acknowledgement

The "Verified datasets" block explicitly states "NO verified source found" for *Arabidopsis thaliana* VOC-related data and CO2 data. Consequently, the project cannot currently answer the real-world biological question of "what drives VOC emissions in Arabidopsis" with real data. The project proceeds with a synthetic dataset to validate the **pipeline logic and statistical methods** only.

### Decision & Rationale

**Decision**: The project will proceed using a **synthetic/mock dataset** generated to strictly adhere to the schema defined in `data-model.md`.

**Rationale**:
1. **No Verified Source**: The "Verified datasets" block explicitly states "NO verified source found" for *Arabidopsis thaliana* VOC-related data and CO2 data.
2. **Spec Requirement**: The spec requires ingestion of *Arabidopsis* data. Since no real data is available in the verified list, a mock dataset is the only way to validate the pipeline logic (ingestion, normalization, imputation, merging, modeling) without violating the "no fabricated URL" rule.
3. **Pipeline Validation**: The mock data will simulate the expected structure (RNA-seq TPM, environmental variables, VOC concentrations) to ensure the code handles edge cases (missing values, unpaired samples, <3 replicates) correctly.
4. **Methodological Simulation**: The synthetic data will be seeded to include known biological relationships (e.g., high expression of specific "gene X" correlates with high VOC "Y") to allow the SHAP/Feature Importance analysis to function as a validation step for the *method's* ability to recover signals, not for biological discovery.

**Methodological Limitation**: Validating feature importance on synthetic data where ground truth is defined by the generator is circular for biological discovery. The goal is **not** to discover real drivers but to verify that the code correctly identifies the seeded signal. The report will explicitly state that high overlap with seeded genes is expected by design (tautology mitigation).

## Statistical Rigor Plan

- **Multiple Comparison Correction**: Feature importance p-values will be derived via permutation testing: generating a null distribution by permuting the target variable (VOC) a sufficient number of times and comparing observed importance against this distribution. The Benjamini-Hochberg procedure (FDR < 0.05) will be applied to these derived p-values as required by Constitution Principle VII.
- **Sample Size/Power**: The synthetic dataset will be generated with N=60 samples. This is below the ideal power for complex genomic studies but sufficient for demonstrating the pipeline and validating the Random Forest algorithm on a CPU. The limitation will be explicitly stated in the report.
- **Dimensionality Reduction**: To mitigate the curse of dimensionality (thousands of genes vs. N=60), gene expression will be aggregated into pathway-level features (e.g., summing TPMs for known Terpene Synthase families) before model training, reducing the feature space to a limited set of features.
- **Causal Inference**: All findings will be framed as **associational**. No causal claims will be made (Constitution Principle VII, FR-009).
- **Measurement Validity**: The synthetic data will use standard units (TPM for RNA, ng/g for VOC) to mimic real-world validity.
- **Collinearity**: The synthetic data generator will introduce known collinearity (e.g., gene A and gene B are highly correlated) to test if the model correctly identifies the relationship as descriptive rather than independent.

## Edge Case Handling

- **<50 Samples**: If the dataset (real or synthetic) has <50 rows, the system will emit a warning and exclude these samples from modeling, as per US-1.
- **Censored Data**: VOC measurements below detection limit will be imputed with a small positive value (e.g., half the detection limit) or excluded if the proportion is high.
- **No Overlap**: If genomic and VOC metadata do not overlap, the system will output an empty dataset and error out gracefully.
- **Missing Gene Family**: If the synthetic data lacks a specific gene family, the overlap statistic will be 0, which will be reported as a descriptive result.