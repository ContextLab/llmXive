# Research: GC Content and Thermal Stability of Archaeal tRNA Stems

## Problem Statement

Archaeal organisms thrive in diverse thermal environments, from mesophilic (<45°C) to hyperthermophilic (≥80°C). A prevailing hypothesis suggests that tRNA stability, mediated by GC content in stem regions (which form three hydrogen bonds per pair vs. two for AU), correlates with the organism's Optimal Growth Temperature (OGT). This project seeks to quantify this correlation using computational sequence analysis, addressing the need for rigorous statistical controls (phylogeny, multiple comparisons, collinearity) and reproducibility.

## Dataset Strategy

The analysis relies on two primary data sources. **tRNA sequences and annotations** are sourced from GtRNAdb. **Host organism metadata (OGT)** is sourced from BacDive or curated literature.

| Dataset | Source / URL | Access Method | Variables Provided | Relevance to FR/SC |
|:--- |:--- |:--- |:--- |:--- |
| **BacDive Genomes** | https://huggingface.co/datasets/hukuang/bacdive_genomes/resolve/main/bacdive_merged.csv | CSV Load | `species_id`, `OGT`, `taxonomy` | FR-002, FR-001, SC-003 |
| **GtRNAdb** | (Primary Source: GtRNAdb Web/API) | HTTP Request / Parsing | `species_id`, `tRNA_sequence`, `stem_regions` (derived) | FR-001, FR-003 |
| **Phylogenetic Trees** | (If available via NCBI/TreeBASE) | Conditional Load | `species_tree` | FR-007, SC-005 |

**Note on Verified Datasets**: The `Verified datasets` block provided in the prompt lists specific URLs for BacDive, OGT, and PIC.
- **BacDive**: The provided URL ` is the primary source for OGT metadata.
- **OGT/Phylogeny**: The provided URLs for OGT (jsonl/parquet) and PIC (parquet) appear to be generic or unrelated to specific archaeal tRNA datasets (e.g., `og_tbe_dataset`, `svla_so100_pickplace`). **Crucially**, these datasets do not contain archaeal tRNA sequences or specific OGT values for the required species.
- **Decision**: The plan will rely on **BacDive** (verified URL) for OGT metadata. For **tRNA sequences**, GtRNAdb is the standard source. Since no verified URL for a pre-packaged "Archaeal tRNA + OGT" dataset exists in the provided block, the implementation will fetch sequences directly from GtRNAdb (as per FR-001) and join with the BacDive metadata. If a specific pre-packaged dataset matching the exact schema is required by the runner, the code will attempt to load from the BacDive CSV and query GtRNAdb for sequences.
- **Dataset Fit**: The BacDive dataset contains OGT. GtRNAdb contains sequences. The join key is `species_id` (or taxonomic name). If a dataset lacks a required variable (e.g., stem annotations), the plan excludes that entry (Edge Case handling).

## Methodology

### 1. Data Retrieval & Preprocessing (FR-001, FR-002, FR-003)
- **Download**: Fetch tRNA sequences for Archaeal species from GtRNAdb.
- **Metadata**: Load OGT from the verified BacDive CSV. Filter for Archaea.
 - **Taxonomic Matching**: Use fuzzy matching (Levenshtein ratio > 0.9) to align species IDs between GtRNAdb and BacDive. If no match is found, fallback to GTDB or curated literature (logged) to ensure N≥30.
- **Parsing**: Use `Bio.SeqIO` and `RNAfold` (ViennaRNA) to predict secondary structure.
 - **Algorithm**: Use Minimum Free Energy (MFE) and partition function.
 - **Fallback**: If `RNAfold` fails or the predicted structure deviates significantly from the standard cloverleaf model (e.g., missing D-arm), use coordinate-based parsing from known tRNA coordinates if available.
 - **Filtering**: Exclude sequences < 60 nt or with ambiguous structure predictions.
- **Feature Engineering**:
 - Calculate GC% for each stem region (D-stem, Anticodon-stem, Acceptor-stem, T-stem).
 - Compute **Composite Stem GC** (mean of all stem GCs) as the primary predictor.
 - Record `tRNA_count` (number of tRNA types) per species for weighting.
- **Filtering**: Exclude species with missing OGT or incomplete stem annotations. Target: ≥30 valid species.

### 2. Statistical Analysis (FR-004, FR-005, FR-006)
- **Primary Model**: **Weighted Least Squares (WLS)** regression of OGT ~ Composite Stem GC.
 - **Weights**: Weight each species by `tRNA_count` to address heteroscedasticity (methodology-f77cf667).
 - **Fallback**: If WLS assumptions fail, use Mixed-Effects Model (species as random effect).
- **Secondary Model**: **LASSO Regression** to identify which specific stem type drives the correlation, penalizing collinearity (scientific_soundness-80b98998).
- **Metrics**: Pearson correlation coefficient (r), p-value, 95% CI.
- **Multiple Comparisons**: Apply Benjamini-Hochberg correction for per-stem descriptive statistics. Note: These are descriptive, not independent hypothesis tests, due to structural coupling.
- **Validation**:
 - **If Tree Available**:
 - **Tree Processing**: Prune tree to species subset. **Ultrametricize** using `dendropy`'s `ultrametricize` method to ensure branch lengths are proportional to time (scientific_soundness-0e504e6e).
 - **PIC**: Compute Phylogenetic Independent Contrasts for GC and OGT. Regress contrasts.
 - **Permutation**: Run **Stratified Permutation** (shuffle within clades). **Constraint**: Minimum clade size = 3. If clades are smaller or tree unresolved, skip stratification and run standard permutation with "Associational" flag.
 - **If No Tree**:
 - **Skip PIC**.
 - **Skip Permutation** (invalid for phylogenetic claims).
 - **Flag**: Explicitly state "CAUTION: Associational findings only; causality not inferred due to lack of random assignment and phylogenetic control." (Constitution VII compliance).

### 3. Phylogenetic Controls & Sensitivity (FR-007, FR-008, FR-009)
- **Tree Subset Strategy**: PIC is applied only to the intersection of species present in both the dataset and the tree. Species not in the tree are excluded from the PIC analysis. The plan mandates reporting the subset N separately and acknowledging potential selection bias (methodology-8c5ab571).
- **Sensitivity**: Sweep minimum sequence length thresholds (, 20, 30 nt) and regression methods (WLS, Huber).
- **Power Analysis**: Calculate **Minimum Detectable Effect Size (MDES)** using the observed variance from the pilot data (or a conservative estimate if N is small) at alpha=0.05 and power=0.80 (methodology-7fa3de3e).
- **Causality Flag**: If no tree is available or random assignment is absent, append the string: "CAUTION: Associational findings only; causality not inferred due to lack of random assignment."

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Addressed via Bonferroni or BH correction (FR-005). Note: Stem types are correlated; tests are descriptive.
- **Sample Size**: Target ≥30. Power calculation is `[deferred]` for exact values but MDES is calculated using observed variance (FR-010).
- **Causal Inference**: Observational study. Claims are strictly associational unless PIC is applied (and even then, confounding is not fully eliminated).
- **Collinearity**: Stem regions are structurally linked. LASSO is used to identify significant predictors while penalizing collinearity.
- **Dataset Validity**: OGT values from BacDive are curated; stem annotations from GtRNAdb are computational predictions. Validation of stem structures is out of scope (assumption in spec).

## Addressing Reviewer Feedback

- **Hydration/Water Activity (Franklin/Pauling)**: This project does not measure melting temperatures in a lab. It correlates *sequence composition* (GC%) with *observed growth temperature* (OGT). The "thermal stability" inferred is the biological adaptation of the organism, not a direct biophysical measurement of tRNA melting under controlled humidity. The analysis is valid as a genomic correlation study.
- **Sample Size (Curie)**: The plan enforces a minimum of 30 species to ensure statistical robustness. MDES is calculated to interpret null results.
- **Helical Parameters (Pauling)**: The analysis uses standard cloverleaf models (fixed geometry) to define stems. Variations in helical parameters (rise per residue) are not explicitly modeled in this phase but are implicit in the sequence-based GC calculation.

## Compute Feasibility

- **Environment**: GitHub Actions (2 CPU, 7GB RAM).
- **Strategy**:
 - No GPU/CUDA required.
 - Libraries: `scipy`, `statsmodels`, `pandas`, `dendropy`, `sklearn` are CPU-efficient.
 - Data: Subset to a small cohort of species; negligible memory footprint.
 - Permutation Test: A sufficient number of iterations is trivial for CPU.
 - Phylogenetic Tree: If available, `dendropy` (CPU) will be used. If not, the fallback path (associational) is executed.
 - **Library Fallback**: Code will attempt `import dendropy`. If `ImportError`, PIC step is skipped, and the "Associational" flag is set immediately.