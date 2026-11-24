# Project Specification: Structure-Only Surrogate Model for 2D Material Elastic Moduli

## 1. Overview

This project implements a **Structure-Only Surrogate Model** to predict the elastic moduli (Young's, Shear, and Poisson's ratio) of 2D materials. The model acts as a fast interpolator of pre‑computed Density Functional Theory (DFT) data, avoiding the computational cost of solving the Schrödinger equation for new candidates while maintaining high accuracy within the training distribution.

**Critical Distinction**: This is **NOT** a first‑principles calculation. It does not solve the Hamiltonian. It is a machine learning model trained on existing DFT results to approximate the mapping from crystal structure to elastic properties.

## 2. Problem Statement

Predicting the elastic moduli of 2D materials is essential for designing flexible electronics, sensors, and composites. Traditional DFT methods are accurate but computationally expensive (hours to days per material). This project aims to reduce inference time to **≤ 200 ms per material on CPU** while achieving a Mean Absolute Percentage Error (MAPE) ≤ 15 % for Young's modulus and shear modulus, and a Mean Absolute Error (MAE) ≤ 0.05 for Poisson's ratio, on held‑out unseen chemical families (see Metric Convention, Section 4a).  

A preliminary verification step will confirm that the chosen data source(s) contain at least **1 000** valid 2D material entries with complete 6‑component elastic tensors; if fewer entries are available, the target count will be adjusted and reported transparently (see FR‑011, FR‑012).

## 3. User Stories

### US1: Data Ingestion and Graph Construction
As a researcher, I want to ingest CIF files and elastic tensors from a single canonical public source (e.g., Materials Project) **and** fall back deterministically to AFLOW or the TMD supplementary dataset if the primary source lacks sufficient 2D entries, so that I can train a model on high‑quality, chemically diverse data.

### US2: Lightweight GNN Training and Evaluation
As a researcher, I want to train a lightweight Graph Neural Network (GNN) on the constructed dataset and evaluate its performance against held‑out DFT values, so that I can verify the model's ability to generalize to unseen chemical families.

### US3: Feature Importance and Ablation Analysis
As a researcher, I want to identify which structural descriptors most strongly influence predicted elastic moduli, so that I can understand the statistical determinants learned by the surrogate model.

## 4. Technical Constraints

- **Memory Target**: The pipeline should aim to keep peak RAM usage ≤ 16 GB on a typical workstation (soft target, not a hard limit).  
- **Compute Environment**: Must run on CPU‑only hardware.  
- **Data Source**: Primary source is **Materials Project**. If the primary source yields < 1 000 valid 2D entries, the pipeline will **deterministically** fall back to the next source in the ordered list: **AFLOW** → **TMD supplementary dataset (arXiv:2505.05891)**. The chosen source and any fallback decision are logged in `data/raw/source_selection.log` for reproducibility.  
- **Terminology**: The terms "First‑Principles" and "Schrödinger Equation" are strictly forbidden when describing the ML model. The model is a "Surrogate" or "Interpolation".

### 4a. Metric Convention

- **MAPE** is applied only to strictly positive target quantities: Young's modulus and shear modulus.  
- **Poisson's ratio** (which may be zero or negative) is evaluated with **MAE**, target ≤ 0.05.  
- This convention applies consistently to the Problem Statement, SC‑002, SC‑005, and SC‑006.

### 4b. Terminology Resolution (Constitution Title Conflict)

The ratified constitution's title ("Predicting the Elastic Moduli of 2D Materials from First‑Principles Calculations") itself contains the term forbidden by Principle VI. This is resolved as follows:

1. The **project title is renamed** to "Predicting the Elastic Moduli of 2D Materials via a Structure‑Only Surrogate Model", and the constitution is amended accordingly through its own Versioning procedure.  
2. **FR‑006's** audit target is the renamed project title and all spec/paper/deliverable titles produced by this project — not the pre‑amendment constitution title. The audit is therefore satisfiable.  
3. Until the amendment is ratified, the constitution title is treated as a historical document identifier, exempt from the terminology audit; the audit records this exemption explicitly in `constitution_title_audit.json`.

## 5. Limitations

**Extrapolation Failure**: The model is a **surrogate interpolator** trained on a specific chemical space defined by the training DFT data. It **cannot** reliably predict properties for:
- Materials with chemical compositions or structural motifs entirely absent from the training set.  
- Extreme conditions (e.g., high pressure, temperature) not represented in the source DFT data.  
- Novel physics outside the scope of the training data's DFT approximations (e.g., strong correlation effects if the training DFT used standard functionals).

**No New Physics Discovery**: The model does not discover new physical laws or solve the underlying quantum mechanical equations. It identifies statistical correlations between structural descriptors (node/edge features) and target elastic moduli. Any "insights" derived from feature importance are correlations, not causal quantum mechanical derivations.

**Data Dependency**: The accuracy of the surrogate is entirely dependent on the quality and coverage of the source DFT data. Errors or biases in the source data will be propagated and potentially amplified by the model.

## 6. Success Criteria

- **SC-001**: Pipeline successfully ingests and processes **≥ 1 000** 2D material entries (or all available valid entries if < 1 000) from the selected source(s) (See US1). The actual count is recorded in `data/results/dataset_summary.json` (see FR‑011).  
- **SC-002**: Model performance is reported on a test set consisting of **unseen chemical families** (defined as a distinct space‑group combined with a cation‑anion stoichiometry class). Baseline comparison to a composition‑only model is **optional**; if performed, results are reported for context but no reduction target is required (See US2, FR‑004).  
- **SC-003**: Model inference time **target** is ≤ 200 ms per material on CPU, measured and reported per FR‑008 (See US2).  
- **SC-004**: Peak memory usage during training, recorded via `tracemalloc` and OS‑level RSS, remains **≤ 16 GB** (soft target, See US2).  
- **SC-005**: Feature importance analysis identifies at least 3 (target 3–5) structural descriptors ranked in the top 5 by permutation importance whose removal degrades Young's/shear MAPE by ≥ 2 percentage points, cross‑checked against SHAP magnitude ranking, and whose cumulative permutation/SHAP contribution accounts for ≥ 70 % of total importance mass (See US3).  
- **SC-006**: The model achieves MAPE ≤ 15 % on Young's modulus and shear modulus, and MAE ≤ 0.05 on Poisson's ratio, on held‑out unseen chemical families, per Constitution Principle VI (See US2).

## 7. Deliverables

1. `data/processed/graphs_v1.parquet`: Processed graph dataset.  
2. `data/results/training_logs.json`: Training metrics and surrogate model disclaimers.  
3. `data/results/generalization_metrics.json`: Intra‑family (optional) and inter‑family performance comparison.  
4. `data/results/feature_importance_report.md`: Unified ranked list of descriptors with ablation deltas.  
5. `docs/methodology.md`: Detailed distinction between DFT and Surrogate methods.  
6. `data/results/constitution_title_audit.json`: Audit result confirming the renamed project title and all project‑produced document titles contain no forbidden "First‑Principles" terminology, including the constitution‑title exemption record (see Section 4b).  
7. `data/processed/split_indices.json`: Train/validation/test split indices generated by clustering on the unified chemical‑family definition.  
8. `data/results/split_validation.json`: Validation metrics for the generated split.  
9. `data/processed/model_v1.pt`: Saved model weights.  
10. `data/results/predictions.json`: Model predictions on the test set.  
11. `code/utils/disclaimer_template.py`: Source file containing the scientific integrity statement and Feynman quote.

### Functional Requirements

- **FR-001**: System MUST ingest CIF files and elastic tensors from a single canonical public source, parse them using `CifParser`, and convert them into graph representations (nodes, edges, features) for training (See US1).  
- **FR-002**: System MUST implement a split generator that **clusters structures by chemical family** (space‑group + cation‑anion stoichiometry) and generates train/validation/test splits, ensuring **no data leakage between families** (See US2).  
- **FR-003**: System MUST train a lightweight GNN on CPU‑only hardware, recording peak memory usage via `tracemalloc` and OS‑level resident set size (RSS), and asserting the recorded peak remains ≤ 16 GB (measurement and assertion, not process‑level enforcement) (See US2).  
- **FR-004**: System MAY evaluate model performance against a composition‑only baseline (e.g., linear regression on Magpie features) and **report** the baseline metrics for context, but it is **not required** to achieve any specific reduction relative to the baseline (See US2).  
- **FR-005**: System MUST compute feature importance using permutation importance and SHAP values, not marginal correlation p‑values. Significance is defined as: removal of the descriptor degrades Young's/shear MAPE by ≥ 2 percentage points, the descriptor ranks in the top 5 by permutation importance, SHAP magnitude ranking agrees, and a permutation test against shuffled targets yields p < 0.05 for the top‑ranked descriptors (See US3).  
- **FR-006**: System MUST generate an audit report (`constitution_title_audit.json`) verifying that the renamed project title (per Section 4b) and all project‑produced document titles contain no forbidden "First‑Principles" terminology, recording the constitution‑title exemption (Constitution Principle VI; anchored to US2 for traceability).  
- **FR-007**: System MUST save model weights, split indices, and validation metrics to the specified output paths (See US2).  
- **FR-008**: System MUST measure and report per‑material CPU inference time for the trained model on the test set, writing the per‑material and median timings to `data/results/generalization_metrics.json`, and verify the **median** is ≤ 200 ms (See US2).  
- **FR-009**: The audit script (`code/utils/verify_constitution_title.py`) MUST write `data/results/constitution_title_audit.json` with a pass/fail record per audited title and exit with code 1 on any failed title check, code 0 otherwise (See US2; supports FR‑006).  
- **FR-010**: System MUST perform 5‑fold cross‑validation over the training + validation pool and report the mean and standard deviation of Young's/shear MAPE and Poisson MAE across folds in `data/results/training_logs.json` (See US2).  
- **FR-011**: System MUST verify that the selected data source(s) contain **≥ 1 000** 2D material entries with complete 6‑component elastic tensors; if the count is lower, the actual number is recorded and downstream success criteria are adjusted accordingly (See SC‑001).  
- **FR-012**: System MUST validate that each ingested entry includes the required columns: CIF structure, space group, 6‑component Voigt elastic tensor, and a flag indicating 2D status. Entries failing this validation are excluded from training but counted in the audit report.  
- **FR-013**: System MUST apply a deterministic source‑selection rule: attempt ingestion from Materials Project first; if the verified entry count after FR‑011/FR‑012 is < 1 000, switch to AFLOW; if still insufficient, switch to the TMD supplementary dataset. The chosen source name and any fallback decision are logged in `data/raw/source_selection.log`.

### Key Entities

- **Structure**: Represents a 2D material crystal structure with lattice parameters, atomic positions, and species.  
- **Graph**: A node‑edge representation of the Structure, where nodes are atoms and edges represent bonds or proximity.  
- **ElasticTensor**: The target property, stored in the 2D (monolayer) convention. All 6 components are recorded — the in‑plane constants C11, C12, C22, C66 plus the out‑of‑plane C13 and C33 retained from the layered supercell — satisfying Constitution Principle VI's 6‑independent‑component completeness filter for data ingestion. For prediction‑target eligibility (deriving Young's modulus, shear modulus, and Poisson's ratio via the standard 2D stiffness‑matrix relations), the 4 in‑plane components (C11, C12, C22, C66) **MUST** be present and finite; entries failing this are excluded from training but retained in the audit of filter pass rates. This reconciles the constitution's 6‑component ingestion filter with the 2D prediction convention.  
- **FeatureDescriptor**: A structural attribute (e.g., coordination number, electronegativity difference) used as a node/edge feature.

## Assumptions

- Users have stable internet connectivity to download data from the canonical source(s).  
- The combined sources (Materials Project, AFLOW, TMD supplement) provide at least **1 000** valid 2D material entries with elastic tensors; if not, the actual count is recorded and downstream targets are adjusted (see FR‑011).  
- Existing authentication system (if any) will be reused; no new auth system is built.  
- The “unseen chemical families” test set is generated by splitting the source data by chemical family (space‑group + cation‑anion stoichiometry), not by arbitrary clustering.  
- **MEGNet benchmark**: The idea's MEGNet benchmark is conditional — it is executed only if a pre‑trained MEGNet checkpoint can run on CPU within the 16 GB memory target; otherwise it is consciously descoped and the descope is recorded in `data/results/training_logs.json`.

# Constitution Compliance Notes

- The constitution title conflict is resolved per Section 4b (Terminology Resolution): project title renamed, constitution amendment initiated via its Versioning procedure, audit target redefined to project‑produced titles.  
- The 6‑component completeness filter of Constitution Principle VI is satisfied at ingestion (all 6 components recorded); the 2D prediction convention requires the 4 in‑plane components for target eligibility (see Key Entities, ElasticTensor).