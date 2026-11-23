# Feature Specification: Predicting Molecular Ionization Energies with Graph Neural Networks

**Feature Branch**: `001-predicting-ionization-energies`  
**Created**: 2026-08-25  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Ionization Energies with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion, Validation, and Proxy Construction (Priority: P1) (US-1)

The researcher needs to download the QM9 dataset, verify the existence of the `homo` column, and construct the target variable "Ionization Energy" using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$), while explicitly validating the approximation's validity on a hold-out subset against literature values before full-scale training.

**Why this priority**: The research question hinges on predicting ionization energy. If the proxy (HOMO) is invalid for this dataset or the data source is inaccessible, the study is untestable. This step resolves the construct validity risk identified in the panel concerns.

**Independent Test**: Can be fully tested by executing the data validation script and verifying that (1) the dataset loads successfully, (2) the `homo` column exists, (3) a calculated $R^2$ **and** MAE between $-\epsilon_{HOMO}$ and literature IE values (from NIST WebBook) on a randomly sampled molecular subset meets thresholds (The model should achieve a high coefficient of determination (R²) **and** MAE ≤ 0.4 eV, and $R^2 \ge 0.9$), and (4) the scaffold-based split is generated.

**Acceptance Scenarios**:

1. **Given** the QM9 dataset URL is accessible, **When** the ingestion script runs, **Then** the system downloads the data and verifies the presence of the `homo` column; if missing, the process halts with a clear error rather than falling back to an unverified proxy.
2. **Given** the loaded data, **When** the validation step runs, **Then** the system computes the correlation ($R^2$) and mean absolute error (MAE) between $-\epsilon_{HOMO}$ and experimental ionization energies from the NIST WebBook for a randomly selected sufficiently large‑molecule subset; if $R^2 < 0.9$ **or** MAE > 0.4 eV, training is aborted with a “Construct Validity Failure” report containing the exact metrics.
3. **Given** the full dataset, **When** the scaffold-based split is applied using Bemis-Murcko scaffolds, **Then** the resulting training, validation, and test sets are disjoint in terms of molecular scaffolds, and the split sizes are at least 10,000 molecules for the training set to ensure statistical power.

*Justification for scope*: High‑level quantum ionization energies are not directly available for the full QM9 corpus. Using the Koopmans‑derived HOMO proxy, **validated** against experimental NIST values (R² ≥ 0.9 and MAE ≤ 0.4 eV), provides a constitution‑compliant surrogate that answers the original research question about ionization energies while preserving scientific rigor.

---

### User Story 2 - CPU-Constrained GNN Training, Retrained Ablation, and Attribution (Priority: P2) (US-2)

The researcher needs to train a Message-Passing Neural Network (MPNN) on the preprocessed data using only CPU resources, and perform ablation studies by **retraining** the model with specific structural features zeroed out (not just inference‑time noise) to determine their predictive contribution, ensuring multiple stochastic runs for statistical validity. The study must also generate attribution maps using Integrated Gradients.

**Why this priority**: This is the core experimental engine. It tests the hypothesis that 2D graphs are sufficient, provides a rigorous feature‑importance assessment, and resolves earlier concerns about inference‑time perturbations versus retraining.

**Independent Test**: Can be tested by running the training script on a standard multi‑core, Adequate RAM CPU runner and verifying that the model converges within the Time limit per job., that the ablation study **re‑trains** the model with the feature removed, and that attribution maps are produced for each ablation configuration.

**Acceptance Scenarios**:

1. **Given** a configured MPNN model and the training set, **When** training starts, **Then** the process completes within 6 hours on a 2‑core, Multi‑GB RAM runner without GPU acceleration.
2. **Given** the trained model and the ablation protocol, **When** the ablation study runs with bond features zeroed out, **Then** the system **re‑trains** the model for each configuration, performing **3 independent stochastic runs** per configuration and recording the MAE distribution for each run.
3. **Given** the MAE distributions from the clean model and each retrained ablated model (3 runs each), **When** the statistical analysis runs, **Then** the system performs a **paired** t‑test on per‑molecule absolute errors across the shared test set, first checking normality with a Shapiro‑Wilk test; if normality fails, a Wilcoxon signed‑rank test is used. The report includes the p‑value **and** Cohen’s d effect size, and provides a post‑hoc power estimate; significance is declared at $p < 0.05$.
4. **Given** an ablation configuration, **When** attribution is requested, **Then** the system computes an **Integrated Gradients** attribution map for the trained model and stores it as an `AttributionMap` linked to the corresponding run (See FR‑011). The method is explicitly defined in `contracts/model_output.schema.yaml`.
5. **Given** the model architecture, **When** training on a batch of multiple molecules, **Then** the CPU memory usage (Peak RSS) remains ≤ 7 GB, and the architecture choice (e.g., GCN, GAT) is documented in the model definition file (See FR‑021).

---

### User Story 3 - Model Evaluation, Baseline Comparison, Error Analysis, and OOD Flagging (Priority: P3) (US-3)

The researcher needs to evaluate the model's performance against a fingerprint-based linear regression baseline, analyze the correlation between prediction errors and molecular properties (size/flexibility), perform a sensitivity analysis on the decision threshold for “success” (e.g., absolute error < 0.4 eV), and flag test molecules whose scaffold was unseen in training.

**Why this priority**: This validates the model's accuracy relative to existing 2D methods, provides chemical intuition, and ensures out‑of‑distribution (OOD) cases are highlighted. It also aligns the success threshold with Constitution Principle VII (MAE < 0.4 eV).

**Independent Test**: Can be tested by executing the evaluation script and verifying that the output includes a comparison table of MAE/RMSE against the baseline, a Pearson correlation coefficient for error vs. flexibility, a sensitivity‑analysis report over the defined threshold set, and an OOD‑flag report.

**Acceptance Scenarios**:

1. **Given** the trained GNN and the test set, **When** evaluation runs, **Then** the GNN's MAE and RMSE are reported alongside the fingerprint‑based linear regression baseline (ECFP fingerprint, radius 2).
2. **Given** the error distribution, **When** analyzed against molecule size, **Then** the system reports the Pearson correlation coefficient between the absolute error and the number of rotatable bonds (flexibility). A magnitude |ρ| ≤ 0.3 (or p > 0.05) is considered acceptable.
3. **Given** the decision threshold for “acceptable prediction” (absolute error < 0.4 eV), **When** the sensitivity analysis runs, **Then** the system sweeps the threshold over the set {0.4, 0.45, 0.5, 0.55, 0.6} and reports the variation in the “success” rate. Variation must stay within ±5 % absolute; larger swings trigger a warning.
4. **Given** the test set, **When** scaffold‑based OOD detection runs, **Then** the system flags any molecule whose Bemis‑Murcko scaffold does not appear in the training set, records the count, and notes the potential for higher prediction error in the final report. OOD molecules must constitute ≤ 10 % of the test set.
5. **Given** the GNN and a DFTB baseline (3‑D physics‑based calculation), **When** residuals are compared, **Then** the system computes the Pearson correlation between GNN residuals and DFTB residuals; a low correlation (|ρ| ≤ 0.2) supports the 2D‑sufficiency hypothesis (See FR‑015).

---

### Edge Cases

- What happens when a molecule in the dataset has an undefined or missing `homo` value? (System must exclude it and log the count; if >5 % of data is excluded, flag a “Data Quality Warning”.)
- How does the system handle a molecule with a non‑standard valence that RDKit cannot parse? (System must exclude it and log the error.)
- What happens if the 6‑hour pipeline time limit is reached before completing all 3 ablation runs? (System must save the best checkpoint from completed runs, report the timeout status, and flag the statistical power as potentially compromised.)
- How does the system handle a test molecule with a scaffold completely unseen in the training set (out‑of‑distribution)? (System must evaluate it but flag the potential for higher error in the final report.) *(now backed by FR‑019/SC‑019)*
- What happens if the calculated $R^2$ between $-\epsilon_{HOMO}$ and literature IE is below 0.9 **or** the MAE exceeds 0.4 eV? (System must halt training and report a “Construct Validity Failure” with the specific metrics.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and parse the QM9 dataset from `https://huggingface.co/datasets/deepchem/qm9`, extracting SMILES and the `homo` column, deriving the target variable as Ionization Energy (IE) using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$). The proxy is stored in the field `negative_homo_proxy` to align with the `dataset.schema.yaml`. The system MUST validate the proxy by computing both $R^2 \ge 0.9$ **and** MAE ≤ 0.4 eV against experimental ionization energies from the NIST WebBook on a randomly sampled 500‑molecule subset (See US-1). If validation fails, the pipeline aborts (see FR‑024).
- **FR-002**: System MUST convert SMILES strings into 2D molecular graph objects using RDKit, extracting atom types, bond types, and functional group fingerprints, ensuring the dataset size is at least 10,000 molecules for the training set (See US-1).  
- **FR-003**: System MUST implement a Message-Passing Neural Network (MPNN) that operates exclusively on CPU, with a configurable batch size **default ≤ 64** (range 1–64) suitable for the experimental setup; the specific architecture (e.g., GCN, GAT) MUST be documented in the model definition file (See US-2).  
- **FR-004**: System MUST perform scaffold-based splitting using Bemis-Murcko scaffolds with an A predominant portion of the dataset will be allocated for training, with smaller portions reserved for validation and testing. to ensure the test set contains chemical scaffolds not present in the training set (See US-1).  
- **FR-005**: System MUST perform ablation studies by **retraining** the model with specific structural features (e.g., bond features) zeroed out during the training process, repeating the process for **3 stochastic runs** per configuration to generate a distribution of MAE values (See US-2).  
- **FR-006**: System MUST compute Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) on the test set and compare them against a fingerprint-based linear regression model (using ECFP fingerprints, radius 2) (See US-3).  
- **FR-007**: System MUST perform a **paired** statistical test on per‑molecule absolute errors between the clean model and each retrained ablated model (3 runs each). Prior to the test, a Shapiro‑Wilk normality check is performed; if normality is rejected, a Wilcoxon signed‑rank test is used instead. The report includes the p‑value **and** Cohen’s d effect size, and provides a post‑hoc power estimate; significance is declared at $p < 0.05$ (See US-2).  
- **FR-008**: System MUST enforce a hard timeout **for each pipeline job** (e.g., data ingestion, main model training, each ablation‑configuration training, evaluation), saving checkpoints if the per‑job limit of 6 hours is reached (See US-2).  
- **FR-009**: System MUST analyze the correlation between the absolute prediction error and molecular size (molecular weight) and flexibility (number of rotatable bonds) and report the Pearson correlation coefficient (See US-3).  
- **FR-010**: System MUST perform a sensitivity analysis on the “success” threshold (absolute error < threshold) by sweeping the threshold over the set {0.4, 0.45, 0.5, 0.55, 0.6} and reporting the variation in success rates (See US-3).  
- **FR-011**: System MUST document the attribution method **Integrated Gradients** in the model definition file and generate an `AttributionMap` for each ablation configuration (See US-2). For validation, a curated subset of aromatic QM9 molecules with known Hammett σ constants will be used; molecules lacking σ are excluded, and the subset is selected via stratified random sampling to avoid bias. Correlation between Integrated Gradients scores and σ values is reported.  
- **FR-012**: System MUST exclude any molecule with a missing `homo` value and log the count; if the exclusion rate exceeds 5 %, the system must flag a “Data Quality Warning” (See US-1).  
- **FR-013**: System MUST ensure the total memory usage (Peak RSS) during the largest batch processing step remains **≤ 7 GB** (See SC-005).  
- **FR-014**: System MUST report the $R^2$ correlation **and** MAE (≤ 0.4 eV) between $-\epsilon_{HOMO}$ and literature IE values as a primary metric of construct validity (See US-1).  
- **FR-015**: System MUST report the Pearson correlation between the GNN residuals and the baseline residuals; a low linear association (|ρ| ≤ 0.2) suggests limited overlap of error sources (See SC-010).  
- **FR-016**: System MUST calculate and report the absolute difference between the Test Set MAE and the Training Set MAE to quantify the generalization gap (See US-3).  
- **FR-017**: System MUST ensure the ablation study includes at least **3 stochastic runs** per configuration to enable valid statistical testing (See US-2).  
- **FR-018**: System MUST perform an a priori power analysis (α = 0.05, desired power ≥ 0.8) to confirm that the training set size (minimum 10,000 molecules) provides sufficient power to detect an MAE difference of a modest magnitude (ΔMAE = 0.1 eV, σ≈0.3 eV). If a timeout forces a fallback to a [deferred]‑molecule subset, the power analysis is recomputed; training proceeds only if power remains ≥ 0.8 (See US-2).
- **FR-019**: System MUST flag any test‑set molecule whose Bemis‑Murcko scaffold was unseen in the training set, record the count, and note the potential for higher prediction error in the final report (See Edge Cases).  
- **FR-020**: System MUST verify the QM9 dataset URL and column schema against the primary source (original QM9 publication) prior to any data processing, and abort with a clear error if the source cannot be validated.  
- **FR-021**: System MUST record the final GNN architecture choice (e.g., GCN vs. GAT, number of layers, hidden dimensions) in the model definition file and ensure this file is the single source of truth referenced by all contracts.  
- **FR-022**: System MUST compare feature‑importance results from the ablation study to established chemical intuition (e.g., known importance of hetero‑atoms or conjugated bonds) and report any discrepancies as a qualitative validation.  
- **FR-023**: System MUST compute the Pearson correlation between GNN residuals and DFTB residuals; a low correlation (|ρ| ≤ 0.2) supports the hypothesis that 2D topology captures most predictive signal without 3D geometry. The DFTB subset used for this analysis is a stratified [deferred]‑molecule sample balanced by scaffold, molecular weight, and flexibility to ensure representativeness.
- **FR-024**: System MUST abort the study if FR‑001 construct‑validity checks fail; no fallback to the proxy is permitted without passing validation.  
- **FR-025**: System MUST orchestrate the overall workflow as separate CI jobs (e.g., data ingestion, main model training, each ablation‑configuration training, evaluation), each respecting the 6‑hour per‑job timeout, thereby allowing the total wall‑clock time to exceed 6 hours while remaining within the resource limits of a free‑tier GitHub Actions runner (See US-2).  
- **FR-026**: System MUST verify external citations and URLs (e.g., QM9 repository, NIST WebBook) against primary sources before use, satisfying Constitution Principle II (Verified Accuracy).

### Key Entities

- **MoleculeGraph**: Represents a molecule with attributes for atom types, bond types, and connectivity, derived from SMILES.  
- **IonizationEnergy**: A scalar value (in eV) representing the target property, derived from HOMO energy using Koopmans' theorem ($IE \approx -\epsilon_{HOMO}$). Stored as field `negative_homo_proxy` to match `dataset.schema.yaml`.  
- **AblationConfig**: Defines which structural features are zeroed out during a specific ablation run.  
- **AttributionMap**: A mapping of atom/bond indices to gradient magnitudes indicating predictive contribution (generated via Integrated Gradients).  
- **ValidationMetric**: Stores the $R^2$ value, MAE, and error margin for the HOMO proxy validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The GNN model must achieve a **MAE reduction of at least 0.05 eV** relative to the fingerprint‑based linear regression baseline **and** the paired‑test p‑value for the improvement must be < 0.05 (See FR‑006, US‑3).  
- **SC-002**: Predictive contribution of a structural feature is considered significant when the ablated model’s MAE increase is **≥ 0.05 eV**, the paired‑test p‑value is < 0.05, and Cohen’s d ≥ 0.5 (See FR‑005, FR‑007, US‑2).  
- **SC-003**: The computational feasibility is measured by the **per‑job** runtime of each pipeline component against a **6‑hour limit** on a **Multi‑core CPU runner with adequate RAM** (See FR‑008, US‑2).  
- **SC-004**: The generalization capability is measured by the observed gap between the Test Set MAE and the Training Set MAE; the absolute gap must be **≤ 0.05 eV** (See FR‑016, US‑3).  
- **SC-005**: The memory efficiency is measured by the peak RAM usage (Peak RSS) during the largest batch processing step against a **7 GB limit** (See FR‑013, US‑2).  
- **SC-006**: The construct validity of the target variable is measured by the $R^2$ correlation **and** MAE (≤ 0.4 eV) between $-\epsilon_{HOMO}$ and experimental ionization energies from the NIST WebBook (See FR‑014, US‑1).  
- **SC-007**: The error‑property correlation is measured by the Pearson correlation between absolute error and molecular size/flexibility; acceptable magnitude is **|ρ| ≤ 0.3** (or non‑significant p > 0.05) (See FR‑009, US‑3).  
- **SC-008**: The robustness of the “success” conclusion is measured by the percentage of test molecules with absolute error **< threshold** across the sweep; variation across thresholds must be within **±5 %** (See FR‑010, US‑3).  
- **SC-009**: The statistical power of the ablation study is measured by the **3 stochastic runs** per configuration and the resulting p‑value and effect‑size distribution; a priori power analysis must confirm **≥ 0.8** power before training (See FR‑018, US‑2).  
- **SC-010**: The error‑overlap analysis is measured by the Pearson correlation between the GNN's residuals and the baseline's residuals; low linear association **|ρ| ≤ 0.2** indicates limited overlap (See FR‑015, US‑3).  
- **SC-011**: The OOD flagging is measured by the count (and proportion) of test molecules whose scaffolds were unseen in training; the proportion must be **≤ 10 %** of the test set (See FR‑019).  
- **SC-012**: The a priori power analysis (FR‑018) must confirm **≥ 0.8** power before training; the recorded analysis outcome is part of the final audit (See US‑2).

## Assumptions

- The QM9 dataset at `https://huggingface.co/datasets/deepchem/qm9` contains the `homo` column and SMILES strings, and is accessible without authentication.  
- The "ionization energy" target is derived from the HOMO energy using Koopmans' theorem; construct validity is **established** by requiring $R^2 \ge 0.9$ **and** MAE ≤ 0.4 eV against experimental IE values from the **NIST WebBook** on a randomly sampled 500‑molecule subset (matched via InChI/SMILES). If this validation fails, the study is halted.  
- The 2D graph representation (atom/bond types) is sufficient to capture the majority of the predictive signal for ionization energy in small, rigid molecules, as hypothesized.  
- The PyTorch Geometric library and RDKit are available and compatible with the free‑tier GitHub Actions runner environment (CPU‑only).  
- The scaffold‑based split successfully separates chemical space such that the test set represents a true out‑of‑distribution challenge for the model.  
- The 6‑hour time limit is sufficient for training a modest MPNN on a subset of QM9 (minimum 10,000 molecules) on a **2‑core CPU with 7 GB RAM**, even with multiple stochastic ablation runs reduced to 3 per configuration. If a timeout forces a fallback to a [deferred]‑molecule subset, a recomputed power analysis (FR‑018) must still meet ≥ 0.8 power; otherwise training aborts.
- No GPU acceleration is available or required; the model must converge using standard single‑precision floating‑point representation on CPU.  
- The fingerprint‑based linear regression baseline (ECFP4, radius 2) provides a valid 2D‑only comparison point for the GNN.  
- The findings of this study are associational, not causal, due to the observational nature of the QM9 dataset (no random assignment of molecular structures).  
- The threshold for “successful prediction” is **MAE < 0.4 eV** as mandated by Constitution Principle VII; the sensitivity analysis will assess robustness around this value.  
- The a priori power analysis (FR‑018) confirms that the chosen training set size (≥ 10,000 molecules) yields ≥ 0.8 power to detect an MAE difference of 0.1 eV at α = 0.05.  
- All dataset URLs and column schemas are verified against the original QM9 publication before any processing (FR‑020).  
- The final GNN architecture (layer type, depth, hidden size) is recorded in the model definition file and serves as the single source of truth for all downstream contracts (FR‑021).  
- Attribution maps are generated exclusively via Integrated Gradients as defined in `contracts/model_output.schema.yaml` (FR‑011).  
- Feature‑importance results are cross‑checked against known chemical intuition; any major discrepancy is reported as a qualitative validation (FR‑022).  
- The DFTB residual correlation analysis (FR‑023) uses a stratified [deferred]‑molecule subset balanced by scaffold, molecular weight, and flexibility to ensure representativeness.
- Principle II (Verified Accuracy) is satisfied by FR‑026, which explicitly verifies external citations and URLs against primary sources.  
