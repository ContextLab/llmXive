# Research: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## Dataset Strategy

The project relies on the **Nazeer et al. DSSC dataset** as the primary source of SMILES and PCE values. The spec assumes the dataset contains all necessary variables. Based on the "Verified datasets" block, the following sources are available. The plan selects the most appropriate verified source that aligns with the "Nazeer et al." description and contains both SMILES and PCE, with explicit provenance checks.

| Dataset Name | Verified URL | Selection Rationale | Variable Fit Check |
|:--- |:--- |:--- |:--- |
| **DSSC-Final-Datasets** | ` | **Primary Candidate.** Contains SMILES and PCE. **Provenance Check:** Must verify if it contains the specific Nazeer et al. data points or is a derivative. If PCE values are synthetic/chatbot-generated without scientific grounding, this dataset will be rejected. | **Verified.** Expected to contain SMILES and PCE. Immediate schema validation (smiles, pce columns) and PCE range check required. |
| **DSSC2024** | ` | **Secondary Candidate.** If DSSC-Final-Datasets lacks scientific metadata or provenance, this dataset will be used. The "test-00000" naming is ignored; content will be inspected for Nazeer alignment. | **Pending.** Requires inspection. |
| **mke-novel-druglike-smiles** | ` | **Rejected.** Contains only SMILES, no PCE values. | **Fail.** Missing target variable. |
| **pcee** | ` | **Rejected.** Likely a different domain (PCE Eval) without the specific DSSC molecular context required. | **Fail.** Likely missing DSSC-specific metadata. |

**Dataset Strategy Decision**: The implementation will attempt to load `DSSC-Final-Datasets.jsonl` first. A **Schema Validation** step will immediately check for `smiles` and `pce` columns and verify PCE values are within a plausible range (0-30%). A **Provenance Verification** step will cross-reference a subset of SMILES/PCE pairs with the known Nazeer et al. publication values (if metadata allows). If validation fails or provenance is weak (e.g., clearly synthetic chatbot data), the pipeline will switch to `DSSC2024`. If neither is suitable, the study will halt with a "Data Unavailable" error.

## Methodology & Statistical Rigor

### Model Architecture
- **GCN**: 2 layers, hidden size 128. This is a minimal architecture chosen specifically to ensure CPU feasibility within the 6-hour limit while retaining sufficient capacity to learn local graph patterns (FR-003).
- **Baseline**: Random Forest with Morgan Fingerprints (radius 2, 2048 bits). This provides a strong, interpretable baseline that is computationally cheap.

### Validation Strategy
- **Scaffold-Aware Split**: Standard k-fold CV is insufficient due to molecular similarity. We will use **Bemis-Murcko scaffolds** to group molecules. Folds will be constructed such that no scaffold in the test set appears in the training set (FR-004). This prevents data leakage and ensures the model generalizes to *new* chemical scaffolds.
- **Scaffold Diversity Risk**: If the dataset has low scaffold diversity, some folds may have <5 samples. In such cases, we will fall back to a **stratified random split** for that specific fold and flag the result as "Low Diversity".
- **Statistical Testing**: Due to the small number of folds (n=5), a **Wilcoxon signed-rank test** (non-parametric) will be used to compare fold-wise MAE of the GCN vs. Random Forest (FR-006). This avoids the normality assumption required by a t-test. We will also report **Cohen's d** (effect size) and a **permutation test** p-value as robustness checks.

### Power Analysis and Statistical Limitations
- **Power**: The dataset size is likely small (<500 molecules, <100 unique scaffolds). This severely limits statistical power. The study is **exploratory** in nature. We will report the effect size (Cohen's d) and confidence intervals to contextualize the significance. If the dataset is too small to detect a meaningful effect, we will explicitly state this limitation rather than claiming a null result.
- **Causality**: The study is observational. We **do not** claim that specific motifs *cause* higher PCE. Claims will be framed as "correlational" or "predictive associations."
- **Collinearity**: Molecular descriptors (e.g., number of atoms vs. molecular weight) are often collinear. The GCN handles this via graph convolution, but the RF baseline may suffer. We will not claim "independent effects" of specific atoms without controlling for the whole graph context.

### Confounding Variable Control
- **Molecular Size**: Larger molecules often have higher PCE due to more light-absorbing units. To prevent identified motifs from being mere proxies for size, we will:
 1. Include **Molecular Weight (MW)** and **Number of Atoms** as features in the Random Forest baseline.
 2. Stratify the scaffold split by MW bins (if possible) or include MW as a covariate in the analysis.
 3. Perform a sensitivity analysis: re-run the model with MW normalized to ensure motifs are not size artifacts.

## Compute Feasibility Analysis

- **Memory**: The dataset is <1GB. Graph generation (RDKit) and GCN training (PyTorch Geometric CPU) for a moderate number of layers and 128 hidden units will easily fit in 7GB RAM.
- **Time**:
 - Data loading/preprocessing: ~ mins.
 - Training (multiple folds, multiple epochs, 2 models): ~2-3 hours on 2 CPU cores.
 - Interpretability (Integrated Gradients/GNNExplainer): A dedicated time allocation.
 - Total estimated time: < 4 hours.
- **Strategy**: A hard timeout wrapper (5h 30m) will be implemented and integrated directly into the training loop to prevent hanging if the dataset is larger than expected or if the CI environment is slow.

## Interpretability Plan

- **Method**: **GNNExplainer** or **Integrated Gradients (IG)** will be applied to the GCN to attribute the prediction to input nodes (atoms).
- **Motif Extraction**: High-attribution nodes will be extracted as subgraphs. We will use a **frequent subgraph mining** approach on these high-importance subgraphs to identify recurring motifs (FR-008).
- **Independent Motif Validation**: To avoid circular validation (motifs derived from overfit models), we will perform a **counterfactual check**: compare the average PCE of molecules containing the identified motif vs. those without, in a held-out subset (or via bootstrapping). If the motif does not correlate with higher PCE in this independent check, it will be discarded.
- **Validation**: Motifs will be visualized and compared against known donor-π-acceptor structures in literature (manual check).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| Dataset lacks PCE column or is synthetic | Fatal | Immediate schema validation and provenance check. Fallback to DSSC2024. |
| SMILES invalid/unparseable | Data Loss | RDKit error handling logs failed molecules to `failed_molecules.log`. |
| Training exceeds 6h | Job Failure | Hard timeout wrapper (5h 30m) triggers graceful shutdown and saves partial artifacts. |
| Scaffold split yields 0 test samples | Fatal | Minimum fold size check; if too few unique scaffolds, fallback to stratified random split with warning. |
| Low statistical power (n=5 folds) | Inconclusive | Report effect sizes (Cohen's d) and use non-parametric tests (Wilcoxon). Frame as exploratory. |