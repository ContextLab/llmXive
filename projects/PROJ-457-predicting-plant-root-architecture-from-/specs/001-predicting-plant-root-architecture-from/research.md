# Research: Predicting Plant Root Architecture from Soil Nutrient Availability

## Research Question
How do soil phosphorus (P) and nitrogen (N) availability levels associate with root architectural traits (total length, branching density, surface area) across multiple plant species in observational datasets?

## Dataset Strategy

| Dataset | Source | Verified URL | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **PlantPheno** | Hugging Face | `https://huggingface.co/datasets/davidkartchner/plant-phenotype/resolve/main/PPR_train_corpus.txt` (and test) | **Verified** | Primary source for root phenotype data. Will be downloaded via `datasets` library or direct URL. |
| **RootReader** | Unknown | **NO verified source** | **Unavailable** | **Deviation**: If no open source is found, this dataset is excluded. The analysis proceeds with PlantPheno only. |
| **ISRIC-World** | Unknown | **NO verified source** | **Unavailable** | **Deviation**: Cannot merge soil data. The plan will attempt to use any soil columns *already present* in PlantPheno. If none exist, the "Soil Nutrient" predictors are dropped, and the model becomes a "Root Trait Distribution by Species" analysis, with FR-002/003 explicitly marked as failed/deviated. |
| **MergedDataset** | Hugging Face | `https://huggingface.co/datasets/blanchon/merged_dataset/resolve/main/data/train-00000-of-00001.parquet` | **Verified** | **Fallback**: If PlantPheno lacks soil data, we check if this dataset contains the required schema (root + soil). If yes, it replaces PlantPheno. If not, we proceed with root-only analysis. |

**Decision/Rationale**:
- **CPU-First**: All planned methods (LMM, Random Forest, KNN imputation, PDP plots) are computationally tractable on CPU. No GPU is required.
- **Data Availability**: The spec requires ISRIC, but it is not verified. The plan explicitly handles this by:
  1. Attempting to fetch soil data from the merged dataset if available.
  2. If no soil data exists, logging a "Data Gap" and proceeding with a reduced model (Species vs. Root Traits only) or dropping the nutrient hypothesis.
  3. **No Fabrication**: We will NOT invent soil data or assume ISRIC exists. If the merged dataset lacks soil columns, the study reframes to "Root Architecture Variation by Species" and notes the inability to test the nutrient hypothesis.

## Statistical Methodology

1.  **Preprocessing**:
    -   **Filtering**: Keep species with $n \ge 20$. Exclude experimental (controlled) data if `data_source_type` is available.
    -   **Transformation**: Log-transform root metrics ($\log(x + \epsilon)$) to reduce skew. Z-score normalize nutrient columns (if present).
    -   **Imputation**: KNN (k=5, Euclidean) for missing values. If neighbors < 5, fall back to mean imputation. If P/N missing entirely, exclude row (deviation from FR-003).

2.  **Modeling**:
    -   **LMM**: `root_metric ~ P + N + (1 | species)`. REML estimation. Satterthwaite for p-values.
    -   **Baseline**: Random Forest (`max_depth=5`).
    -   **Validation**: 5-fold CV split by **species** (Constitution Principle VI).
    -   **Correction**: Bonferroni correction for multiple comparisons across traits/species.

3.  **Validation & Rigor**:
    -   **Causal Framing**: All results framed as associational (FR-009).
    -   **Sensitivity**: Compare coefficients against literature ranges (FR-011). *Note: If no verified literature source is found, this step will be marked as "Not Verified" rather than using hardcoded values.*
    -   **Collinearity**: Check VIF for P and N. If definitionally related, report descriptive stats only.

## Compute Feasibility
-   **RAM**: Estimated < 4 GB for datasets < 100k rows.
-   **Time**: < 2 hours for full pipeline on 2 CPU cores.
-   **GPU**: Not required.

## Risks & Mitigations
-   **Risk**: No soil data available in any verified source.
    -   **Mitigation**: Pivot to species-level analysis; document as a "Data Availability Limitation" in the final report.
-   **Risk**: ISRIC data required by spec is missing.
    -   **Mitigation**: Log AM-001 deviation; proceed with available data or halt nutrient analysis.
