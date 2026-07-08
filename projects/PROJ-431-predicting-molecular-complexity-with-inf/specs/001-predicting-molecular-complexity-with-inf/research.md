# Research: Predicting Molecular Complexity with Information Theory

## 1. Scientific Rationale

This project investigates the hypothesis that information-theoretic descriptors of molecular graphs—specifically Shannon entropy derived from atom and bond degree distributions—correlate with physicochemical properties critical to drug discovery: aqueous solubility (logS) and membrane permeability (logP).

While the spec assumes a correlation exists, the research phase validates the *feasibility* of computing these descriptors on available datasets and confirms that the datasets contain the necessary variables. As noted by reviewer `john-von-neumann-simulated`, the distinction between "structural information" (topological complexity) and "functional information" (biological activity) is critical. Here, we operationalize "structural information" strictly as the Shannon entropy of the degree distribution of the molecular graph, avoiding ambiguous algorithmic complexity measures.

**Addressing Confounding**: A primary scientific risk is that observed correlations are driven by molecular size (Molecular Weight, MW) rather than topological complexity, as both entropy and solubility/permeability are strongly correlated with size. This plan addresses this by:
1. Computing MW and Atom Count for every molecule.
2. Training a baseline Ridge Regression model using only MW and Atom Count.
3. Comparing the Entropy model's performance against this baseline.
4. Computing partial correlations controlling for MW.

If the Entropy model does not outperform the MW-only baseline, the result is interpreted as "Entropy does not add predictive value beyond size," which is a valid scientific finding.

## 2. Dataset Strategy

The implementation requires a dataset containing:
1. **SMILES strings**: To reconstruct molecular graphs.
2. **logS values**: Experimental aqueous solubility.
3. **logP values**: Experimental octanol-water partition coefficient.

### Verified Sources
Per the project constraints, we utilize the following verified datasets from the "Verified datasets" block.

*Note: A critical gap analysis was performed. The `medical-5day` datasets focus on medical text generation and lack molecular graph data. The `rdkit_chemical` and `chembl-2025` datasets are the primary candidates.*

| Dataset Name | Verified URL | Contains SMILES? | Contains logS? | Contains logP? | Suitability |
|:--- |:--- |:--- |:--- |:--- |:--- |
| **ChEMBL-2025 Randomized** | ` | **Yes** | **Yes** (likely in descriptors) | **Yes** (likely in descriptors) | **Primary Candidate** |
| **Half-ChEMBL-2025** | ` | **Yes** | **Yes** | **Yes** | **Fallback / Larger Sample** |
| **RDKit Chemical** | ` | Yes | Unknown | Unknown | **Secondary** (Requires schema check) |
| **Medical-5day** | (Various) | No | No | No | **Excluded** (Irrelevant domain) |

**Decision**: The `chembl-2025-randomized-smiles-cleaned-rdkit-descriptors` dataset is selected as the primary source. It is explicitly named with "rdkit-descriptors," suggesting pre-computed features, but the implementation will **re-calculate entropy from raw SMILES** to ensure consistency with the spec's definition (FR-002, FR-003). If logS/logP are missing in this specific parquet file, the `half-of-chembl` variant will be used as it likely contains a broader set of properties.

**Variable Fit Check**:
- **Predictors**: Atom/Bond Entropy (Computed from SMILES).
- **Outcomes**: logS, logP (Must exist in the dataset columns).
- **Action**: The `data-model.md` will define the exact column mapping. **Mandatory Schema Verification**: The pipeline will abort if `smiles`, `logS`, or `logP` are missing. If the dataset lacks these, the plan will fail the "Dataset-variable fit" check, and the spec will need to flag a gap. *Assumption for planning*: The ChEMBL-derived datasets contain these standard physicochemical properties.

## 3. Statistical Methodology

### 3.1 Entropy Calculation (FR-002, FR-003)
Shannon entropy $H$ will be computed for the degree distribution of atoms and bonds:
$$ H = - \sum_{i} p_i \log_2(p_i) $$
Where $p_i$ is the proportion of atoms (or bonds) with degree $i$.
- **Atom Entropy**: Based on the number of non-hydrogen neighbors (degree) for each atom in the RDKit molecule object.
- **Bond Entropy**: Based on the bond order/type distribution.
- **Handling**: Molecules with no bonds (single atoms) will result in $H=0$.
- **Re-computation**: Even if the dataset contains pre-computed entropy columns, the pipeline will ignore them and compute fresh values from SMILES to satisfy FR-002/003.

### 3.2 Regression & Hypothesis Testing (FR-006, FR-010)
- **Model**: Ridge Regression (Linear) with $\alpha=1.0$.
- **Split**: [deferred] Train / [deferred] Test, seed=42.
- **Metrics**: RMSE and Pearson $r$.
- **Hypothesis Tests**: 4 tests total (Atom-logS, Atom-logP, Bond-logS, Bond-logP).
- **Null Hypothesis**: $H_0: r = 0$.
- **Correction**: Bonferroni correction applied. Significance threshold $\alpha_{adj} = 0.05 / 4 = 0.0125$.
- **Sensitivity**: Benjamini-Hochberg (FDR) adjusted p-values will also be reported.
- **Causal Claim**: None. The study is observational. Claims will be strictly associational ("correlates with").

### 3.3 Baseline & Confounding Control
- **Baseline Models**:
 1. **Null**: Predict mean of training target.
 2. **Size**: Ridge Regression using only Molecular Weight (MW) and Atom Count.
- **Comparison**: The Entropy model's RMSE and $r$ will be compared against the Size baseline.
- **Partial Correlation**: Compute partial correlation between Entropy and Target, controlling for MW and Atom Count.

### 3.4 Sensitivity Analysis (FR-011)
- **Sweep**: $\alpha \in \{0.1, 1.0, 10.0\}$.
- **Stability Metric**: Relative range of RMSE and $r$ across the sweep must be $< 10\%$.

## 4. Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
- **Strategy**:
 - Use `pandas` for data manipulation (efficient for <10k rows).
 - Use `rdkit` for graph parsing (CPU-only, no GPU required).
 - Use `scikit-learn` for Ridge Regression (CPU-optimized).
 - **Memory**: [deferred] molecules in a DataFrame with ~10 columns is < 1 MB. Even with full molecular graph objects, memory usage will stay well under 2 GB.
 - **Time**: RDKit parsing is fast (~1-5 ms per molecule). 10k molecules $\approx$ 30-60 seconds. Entropy calculation adds negligible overhead. Total pipeline < 5 minutes.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset lacks logS/logP** | **Fatal**: Cannot train model. | **Mandatory Schema Verification**: Pipeline aborts with clear error if columns missing. |
| **Malformed SMILES** | Data loss. | FR-008 handles this: log warning, skip row, continue. |
| **Collinearity** | Atom and Bond entropy may be highly correlated. | Report correlation; use FDR adjustment; run multivariate model. |
| **Weak Correlation (|r| < 0.3)** | Fails SC-001/006/008/009 (Spec Target). | **Scientific Validity**: Report observed values. Valid result is "No correlation found." |
| **Entropy adds no value beyond MW** | Fails scientific hypothesis. | **Baseline Comparison**: If Entropy model <= MW baseline, report "Entropy adds no value." Valid scientific result. |
| **Pre-computed entropy in dataset** | Invalidates "compute" requirement. | **Re-computation**: Pipeline ignores pre-computed columns and calculates from SMILES. |