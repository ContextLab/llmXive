# Feature Specification: Predicting Molecular Interactions in Polymer Blends Using Machine Learning

**Feature Branch**: `feature/001-predict-polymer-blend`  
**Created**: 2026-10-24  
**Status**: Draft  
**Input**: User description: *“Identify which molecular structural features drive the deviation of experimental polymer‑blend Hansen solubility parameters from linear mixing‑rule predictions, and quantify the predictive signal of these non‑linear contributions.”*  

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify non‑linear deviation drivers (Priority: P1)

A materials researcher wants to run an end‑to‑end analysis that (a) computes the linear‑mixing prediction for each blend, (b) trains a lightweight graph‑convolutional network on the residual (ΔHSP), (c) evaluates the model, and (d) reports the structural descriptors that most strongly explain the residual variance.

**Why this priority**: This story delivers the core scientific contribution – a reproducible pipeline that both predicts the residual and reveals the underlying structural drivers, directly answering the research question.

**Independent Test**: The entire workflow can be executed on the CI runner using only the supplied dataset. Successful completion produces a report containing (i) R² ≥ 0.40, (ii) a paired‑t‑test p‑value < 0.05 against the null model, and (iii) at least two ranked descriptors with meaningful SHAP importance.

**Acceptance Scenarios**:

1. **Given** a curated dataset of 500 homopolymers and 100 blends with experimental HSP values, **when** the pipeline is invoked, **then** it computes linear‑mixing predictions, derives ΔHSP, trains the GCN, and outputs a JSON file with model performance metrics and a CSV of SHAP‑ranked descriptors.  
2. **Given** the same dataset, **when** the pipeline finishes, **then** the total wall‑clock time is ≤ 6 hours and peak RAM usage is ≤ 7 GB on a 2‑core GitHub Actions runner.  

### Edge Cases

- **Missing SMILES**: If a component lacks a valid SMILES string, the pipeline logs a warning, skips that blend, and continues without aborting.  
- **Zero volume fraction**: Blends where a component’s volume fraction φ = 0 are ignored in linear‑mixing calculations and reported in an “excluded blends” summary.  
- **Non‑experimental HSP**: If a homopolymer’s HSP entry is flagged as “estimated” rather than measured, the entry is excluded from residual computation and documented in the audit log.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (See US-1): The system MUST compute linear‑mixing HSP predictions for each blend using the formula δ_blend = Σ φ_i · δ_i.  
- **FR-002** (See US-1): The system MUST calculate the Euclidean deviation vector ΔHSP between experimental and linear‑mixing HSP values for every retained blend.  
- **FR-003** (See US-1): The system MUST train a CPU‑optimized 3‑layer Graph Convolutional Network (GCN) on the residual ΔHSP target, using graph‑level descriptors derived from component SMILES via RDKit.  
- **FR-004** (See US-1): The system MUST evaluate the trained model on a held‑out test split and report R² and MAE against the ΔHSP ground truth.  
- **FR-005** (See US-1): The system MUST perform a paired two‑sample t‑test comparing model predictions to a null model that always predicts zero deviation; the test result (p‑value) must be recorded.  
- **FR-006** (See US-1): The system MUST compute SHAP values for the trained GCN and output a ranked list of global graph descriptors with their mean absolute SHAP scores.  
- **FR-007** (See US-1): The system MUST enforce a runtime budget of ≤ 6 hours and a memory ceiling of ≤ 7 GB on a 2‑core CPU‑only runner; exceeding either aborts the job with a clear error message.  
- **FR-008** (See US-1): The system MUST log all intermediate artefacts (linear predictions, ΔHSP vectors, model checkpoints) and package the final report (metrics + SHAP table) as reproducible artifacts in the CI workspace.  

### Clarification Needed

- **FR-009**: [NEEDS CLARIFICATION: Are all homopolymer HSP entries in the source dataset experimentally measured, or are some derived from group‑contribution estimates?]  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (See US-1): Test‑set R² ≥ 0.40, demonstrating that the GCN captures ≥ 40 % of residual variance.  
- **SC-002** (See US-1): Test‑set MAE ≤ 0.15 (ΔHSP units), indicating practical predictive accuracy.  
- **SC-003** (See US-1): Paired t‑test p‑value < 0.05, confirming that the model’s predictions are statistically better than the null.  
- **SC-004** (See US-1): At least two structural descriptors have mean absolute SHAP ≥ 0.05 (relative importance), satisfying the “identify 2‑3 drivers” expectation.  
- **SC-005** (See US-1): End‑to‑end pipeline completes within 6 hours wall‑clock time on the specified runner.  
- **SC-006** (See US-1): Peak memory consumption does not exceed 7 GB.  
- **SC-007** (See US-1): No GPU‑specific libraries (e.g., CUDA, bitsandbytes) are imported; the code runs on pure CPU.  

## Assumptions

- The Polymer Database and HuggingFace *polymer‑hsp* dataset provide experimentally measured δ_D, δ_P, and δ_H for both homopolymers and blends.  
- Each blend entry includes valid volume fractions (Σ φ_i = 1) and SMILES strings for all components.  
- The residual ΔHSP is a valid target for regression; i.e., experimental measurement error is small enough that systematic structural effects are detectable.  
- The chosen 3‑layer GCN (≤ 200 k parameters) fits comfortably in ≤ 7 GB RAM when processing batches of size 16 and graph depth ≤ 10.  
- SHAP analysis on a GCN can be approximated with KernelSHAP (CPU‑only) without requiring GPU acceleration.  
- Multiple‑comparison correction is not needed beyond the paired t‑test because only a single primary hypothesis (model vs null) is evaluated; descriptor ranking is exploratory and reported descriptively.  
- All software dependencies (RDKit, PyTorch CPU, scikit‑learn, shap) are installable from PyPI without custom compiled extensions that would exceed the runner’s storage limits.  

--- 

*End of Specification*
