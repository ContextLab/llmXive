# Research: Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

## 1. Dataset Strategy

The project relies on publicly available metabolomic datasets. However, a critical constraint identified in the specification is the need for **paired** pre-stress profiles and post-stress recovery metrics (≥7 days) from the **same samples**.

### Verified Datasets Analysis
The following datasets were verified for reachability and format. **Crucially, none of the verified datasets listed in the `# Verified datasets` block contain plant metabolomic data with paired stress/recovery metrics.**

| Dataset Name | Source URL | Format | Relevance to Spec |
|:--- |:--- |:--- |:--- |
| NCBI Disease | ` | Zip | **Irrelevant**. Human disease text data. |
| HERCULES (Australia) | ` | CSV | **Irrelevant**. Road sequence/traffic data. |
| Pandaset | ` | Zip | **Irrelevant**. Autonomous vehicle sensor data. |
| Geometry3k | ` | Parquet | **Irrelevant**. Math problem solving. |
| Agriculture QA | `https://huggingface.co/datasets/KisanVaani/...` | Parquet | **Irrelevant**. Text-based QA, not metabolomic profiles. |
| C4 News | `https://huggingface.co/datasets/bs-modeling-metadata/...` | Parquet | **Irrelevant**. News text. |
| MUSTC | `https://huggingface.co/datasets/kudo-research/...` | Parquet | **Irrelevant**. Speech-to-text. |
| Mosquito Data | `https://huggingface.co/datasets/TheNoob3131/...` | CSV | **Irrelevant**. Vector data, not plant metabolomics. |
| IMaSC / MSC | `https://huggingface.co/datasets/thennal/...` | Parquet | **Irrelevant**. Medical/Social science text. |
| Elsevier OA | `https://huggingface.co/datasets/orieg/...` | JSON | **Irrelevant**. Bibliographic metadata. |
| LODO (KVKK) | `https://huggingface.co/datasets/lodosNova/...` | Parquet | **Irrelevant**. Legal text (Turkish). |

### Critical Mismatch & Plan Adjustment
**Fatal Gap Identified**: The specification requires "publicly available metabolomic datasets from NCBI GEO, Zenodo" containing **paired** pre-stress and post-stress recovery data. The **verified dataset block provided for this project contains NO plant metabolomic data**. The available datasets are text, traffic, or unrelated scientific data.

**Decision**:
1. **Do NOT proceed with data ingestion of the verified list** as it does not meet the "Dataset-variable fit" requirement (missing the outcome variable entirely).
2. **Plan Adjustment**: The implementation plan will use a **Mechanism-Guided Synthetic Generator**. This is not "random" synthetic data. It is a controlled simulation where:
 * **Ground Truth**: The recovery index is generated as a known function of specific stress-pathway metabolites (e.g., `Recovery = 0.5 * Proline + 0.3 * ABA + Noise`).
 * **Stress Vectors**: Distinct stress types (Drought, Salinity) are simulated with different metabolite signatures to allow valid cross-stress testing.
 * **Heterogeneous Metrics**: The generator produces "biomass", "survival", and "chlorophyll" columns with different scales to exercise the FR-002.1 normalization logic.
 * **Purpose**: This allows the pipeline logic (FR-001 to FR-012) to be validated against a known biological ground truth, ensuring that the "Biological Plausibility" and "Cross-Stress Generalizability" checks are meaningful tests of the code, not circular checks of random data.
3. **Scope**: The project is explicitly scoped as a **Pipeline Validation Study**. The scientific claim is not "We discovered new biomarkers" but "We validated a pipeline capable of recovering known biomarkers from mechanism-guided data." If a real dataset is required for the final paper, the project must pause at `planned` until a verified URL for a plant metabolomic dataset with paired recovery metrics is added to the `# Verified datasets` block.

**Alternative Strategy**: If a real dataset is required for the final paper, the project must pause at `planned` until a verified URL for a plant metabolomic dataset with paired recovery metrics is added to the `# Verified datasets` block.

## 2. Methodological Rigor

### Statistical Approach
- **Models**: Random Forest (RF) and Support Vector Machine (SVM) with RBF kernel.
 - *Rationale*: CPU-tractable, robust to noise, provide feature importance (RF) or margin analysis (SVM).
- **Cross-Validation**: 5-fold CV for in-distribution performance.
- **Generalizability**:
 - **Cross-Stress**: Train on Drought (simulated vector A), Test on Salinity (simulated vector B).
 - **LODO**: Leave-One-Dataset-Out (simulated by splitting synthetic data into virtual datasets with distinct noise profiles).
- **Significance**: Permutation testing (n=1000) to establish p-values against the null hypothesis (random labels).
- **Metric Selection**:
 - **Individual Level**: $R^2$ (Coefficient of Determination).
 - **Population Level**: Pearson correlation coefficient ($r$) (as per FR-011).

### Addressing Rigor Concerns
1. **Multiple Comparisons**: If testing multiple stress pairs, apply Bonferroni correction to p-values.
2. **Sample Size/Power**: Acknowledged limitation. With public data, sample sizes may be small ($N < 50$ per stress type). The plan will report power limitations explicitly.
3. **Causal Inference**: The study is **observational**. Claims will be framed as "associational" or "predictive signal," not causal effects.
4. **Collinearity**: Metabolites are often correlated. RF handles this via feature importance, but independent effects cannot be claimed. We will report "predictive contribution" rather than "independent effect."
5. **Missing Data**: Strict <10% threshold (FR-003). If >10%, dataset is rejected. Imputation: Half-minimum method. Transformation: $\ln(x)$.

### Biological Validation
- **Mapping**: Map metabolite names to KEGG Compound IDs.
- **Enrichment**: Compare top-ranked features against known stress pathways (Osmolytes, Antioxidants).
- **Threshold**: Jaccard similarity $\ge 0.3$ or Enrichment p-value $< 0.05$.
- **Ground Truth**: The synthetic generator will embed specific KEGG pathways (e.g., Proline biosynthesis) as the predictive signal, allowing the validation step to confirm if the pipeline correctly identifies these known pathways.

## 3. Compute Feasibility

- **Constraint**: 2 CPU cores, 7GB RAM, 6 hours.
- **Strategy**:
 - **Data Subsampling**: If a dataset exceeds a manageable size, sample rows to fit memory.
 - **Model Complexity**: RF with `n_estimators=100` (default), SVM with `C=1.0`. Avoid grid search over large ranges.
 - **Permutation Test**: Run on a subset of features or parallelize via `n_jobs=2` (max cores).
 - **Memory Management**: Use `pandas` chunking for ingestion.

## 4. Decision Log

| Decision | Rationale |
|:--- |:--- |
| **Use Mechanism-Guided Synthetic Generator** | No verified plant metabolomic dataset exists in the provided list. A simple random generator would fail biological validation. This generator embeds known pathways as ground truth to allow meaningful testing. |
| **Reject Verified List for Research** | None of the verified URLs contain plant metabolomics. Using them would violate "Dataset-variable fit". |
| **Switch to Population-Level Correlation** | If paired time-series are unavailable in synthetic data, fallback to group means (FR-009). |
| **No GPU/CUDA** | Free-tier runner has no GPU. All models are CPU-optimized. |
| **Simulate LODO via Virtual Datasets** | To test FR-010 without multiple real datasets, the synthetic generator will create virtual datasets with distinct noise profiles. |
| **Simulate Heterogeneous Metrics** | To test FR-002.1, the generator will produce biomass, survival, and chlorophyll columns with different scales. |
