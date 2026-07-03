# Research: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## 1. Dataset Strategy

The project requires genomic data (SNPs) and phenotype metadata (CCD status, covariates).

| Dataset | Source Type | Verified URL | Status | Notes |
|---------|-------------|--------------|--------|-------|
| **Honeybee Genomics** | NCBI BioProject (PRJNA639195, PRJNA566029) | **NO verified source found** | **Critical Gap** | The spec requires this data. However, the `# Verified datasets` block explicitly states "NO verified source found" for BioProject. **Plan:** The pipeline will implement `FR-001` to *attempt* download with SSL verification. If download fails or data is missing, the system will generate a **synthetic dataset** (including simulated FASTQ) matching the `contracts/dataset.schema.yaml` to validate the pipeline logic. The final paper will explicitly state that results are based on synthetic data due to lack of verified public access. |
| **BeeBase Metadata** | BeeBase Repository | **NO verified source found** | **Critical Gap** | Same as above. Covariates (Varroa load, region) will be simulated to match the schema if the real source is unreachable. |
| **SNP (Reference/Testing)** | HuggingFace (ManuBansal) | ` | **Verified** | This dataset contains human SNP data (33 param). **Incompatibility:** It is NOT honeybee data. It cannot be used for the biological analysis. It is listed here only to confirm no *honeybee* SNP data is available in the verified block. |
| **NCBI Disease** | HuggingFace (pie) | ` | **Verified** | Contains dummy disease data. **Incompatibility:** Not honeybee genomic data. |
| **CCD (Text)** | HuggingFace (ccdv) | ` | **Verified** | Contains text data (arxiv/gov report). **Incompatibility:** Not genomic. |

**Decision**: Since **NO verified source** exists for the required *Apis mellifera* genomic data or BeeBase metadata in the provided list, the implementation **MUST** proceed with a **Synthetic Validation Strategy**. The pipeline will:
1. Attempt real data download (FR-001).
2. If failed, generate synthetic VCF and Phenotypes.
3. Generate **Simulated FASTQ** reads from the synthetic VCF (using `dwgsim` logic) to satisfy FR-002 (Alignment/Calling).
4. Run the full GWAS and ML pipeline on this synthetic data.
5. Frame results strictly as **Pipeline Validation** (measuring False Positive/Negative rates against injected signal) rather than biological discovery.

**Dataset Variable Fit**:
- **Required**: `colony_id`, `health_status` (CCD/Healthy), `geographic_region`, `sampling_year`, `Varroa_mite_count`, `SNP` (rs_id, chr, pos, ref, alt).
- **Synthetic Strategy**:
 - Generate colonies (a substantial number of CCD, 50 Healthy).
 - Assign covariates randomly but with realistic distributions (e.g., Varroa count ~ Poisson).
 - Simulate a subset of SNPs for CPU feasibility.
 - **Signal Injection**: Inject 5 SNPs with **OR=5.0** (extreme effect) to ensure detection is possible given the low power. This allows validation of the pipeline's ability to find strong signals, while explicitly acknowledging that real-world OR=2.5 signals are undetectable.
 - **Phenotype Harmonization**: Map synthetic `health_status` to the 'CCD Working Group (2007)' criteria (dead adults, no pupae, <10% population) to satisfy FR-011.

## 2. Statistical Rigor & Methodology

### 2.1 Multiple Testing Correction
- **Method**: **Bonferroni correction based on Effective Number of Independent Tests (Me)**.
- **Rationale**: BH applied to a pruned subset is invalid for GWAS FDR control due to LD. The plan calculates Me via spectral decomposition of the LD matrix (using `scikit-allel` or similar).
- **Primary Threshold**: $p < \alpha / Me$ (FWER control).
- **Exploratory**: BH q-values ($q < 0.05$) are reported for ranking but **not** used as the primary significance claim.
- **Sensitivity**: Sweep the Bonferroni threshold (e.g., $\alpha/Me$, $\alpha/Me \times 2$) to assess robustness.
- **Clarification**: The plan distinguishes between FWER (Bonferroni) for discovery claims and FDR (BH) for exploratory ranking, avoiding the conflation of these concepts.

### 2.2 Power Analysis & Sample Size
- **Requirement**: `FR-012` and `US-2`.
- **Method**: Calculate power for detecting OR=5.0 (synthetic signal) at $\alpha=0.05$ (Bonferroni-adjusted) with n=120.
- **Halt Condition**:
 - If `n < 80`: HALT with `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 - If `n >= 80` but `Power < 20%`: HALT with `ERR_POWER_INSUFFICIENT`.
- **Note**: With n=120, the study is **severely underpowered** for genome-wide discovery of OR=2.5. The pipeline will explicitly report this limitation. The synthetic validation uses OR=5.0 to demonstrate that the pipeline *can* detect strong signals if they exist.

### 2.3 Causal Inference & Observational Design
- **Constraint**: `FR-009` and `US-2`.
- **Statement**: All findings are **ASSOCIATIONAL**. No randomization exists.
- **Reporting**: The output `results_summary.md` will include a disclaimer: "These results represent statistical associations between SNPs and CCD status. Causal inference is not supported due to the observational nature of the study and potential confounding."
- **Synthetic Context**: For synthetic data, the "ground truth" is known, allowing calculation of False Positive/Negative rates, but this does not validate biological discovery in the real world.

### 2.4 Measurement Validity
- **Instruments**: CCD diagnosis criteria harmonized to "dead adult bees, no dead pupae, <10% population" (Spec Assumption).
- **Validation**: Synthetic data generator will strictly apply this binary definition. The code will log the mapping logic to satisfy FR-011.

### 2.5 Predictor Collinearity & Population Structure
- **Covariates**: `geographic_region` and `sampling_year`.
- **Risk**: Regions may be confounded with years (e.g., specific regions sampled only in specific years).
- **Solution**: **Principal Component Analysis (PCA)**.
 - Compute top PCs from the genotype matrix.
 - Include PCs as covariates in the PLINK model.
 - **Conditional Covariates**: If VIF for `region` or `year` > 5, exclude them from the model and rely on PCs alone. If VIF < 5, include them.
- **Diagnostic**: Compute Variance Inflation Factor (VIF) and correlation matrix (`FR-010`, `US-3`).
- **Action**: If collinearity is high, interpret coefficients as "joint effects" or rely on PC adjustment.

## 3. Compute Feasibility (CPU-Only)

- **Hardware**: 2 CPU, 7 GB RAM.
- **Strategy**:
 - **Data Subsetting**: Use [deferred] SNPs (instead of 1M) for the primary run to ensure < 6h runtime.
 - **Tools**:
 - `bwa mem` / `FreeBayes`: CPU-efficient for small subsets.
 - `PLINK 2.0`: Optimized for binary format, low memory footprint.
 - `scikit-learn`: CPU-only LASSO (`LogisticRegressionCV` with `penalty='l1'`).
 - **No GPU**: Explicitly avoid any CUDA-dependent libraries.
 - **Simulated FASTQ**: Use a lightweight simulator (e.g., `dwgsim` or custom Python script) to generate reads, avoiding the need for real FASTQ.

## 4. Dataset & Variable Mapping (Synthetic)

Since real data is unavailable (Verified Datasets check), the following mapping is used for the synthetic generator:

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `colony_id` | String | Synthetic | Unique identifier (e.g., "COL_001") |
| `health_status` | Binary (0/1) | Synthetic | 1=CCD, 0=Healthy (Mapped to CCD 2007 criteria) |
| `geographic_region` | Categorical | Synthetic | "North", "South", "East", "West" |
| `sampling_year` | Integer | Synthetic | 2020, 2021, 2022 |
| `Varroa_mite_count` | Integer | Synthetic | Poisson distributed (λ=5) |
| `SNP_rs_id` | String | Synthetic | "rs_1001", "rs_1002"... |
| `SNP_chrom` | Integer | Synthetic | 1-16 (Honeybee chromosomes) |
| `SNP_pos` | Integer | Synthetic | Random position within chromosome |
| `SNP_ref` | String | Synthetic | A, C, G, T |
| `SNP_alt` | String | Synthetic | A, C, G, T (different from ref) |
| `PC1`...`PC10` | Float | Derived | Principal Components for population structure |
