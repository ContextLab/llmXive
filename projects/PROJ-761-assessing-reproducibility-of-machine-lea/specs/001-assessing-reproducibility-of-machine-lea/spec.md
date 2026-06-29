# Feature Specification: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

**Feature Branch**: `[PROJ-761-01-reproducibility]`
**Created**: 2026-06-25
**Status**: Draft
**Input**: User description: "Assessing reproducibility of machine‑learned reaction yield models"

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Reproduce Reported Metrics (Priority: P1)

A researcher wants to know, for each selected publication, how closely an independent re‑implementation matches the originally reported performance metrics (MAE, R², Spearman ρ).

**Why this priority**: Establishing a per‑paper reproducibility score is the core deliverable; without it the study cannot answer its primary research question.

**Independent Test**: Run the pipeline on a single target paper, retrieve its dataset split and hyper‑parameters, train the model on the free‑tier CI runner, compute the three metrics and compare them to the numbers reported in the paper.

**Acceptance Scenarios**:

1. **Given** a paper that provides a public dataset split and a complete hyper‑parameter list, **when** the pipeline is executed, **then** the system outputs reproduced MAE, R², and Spearman ρ together with the absolute deviation from the reported values.
2. **Given** a paper that omits a random‑seed specification, **when** the pipeline is run, **then** the system records the seed it used (default = 42) and flags the missing information in the results log.

---

### User Story 2 – Quantify Agreement Across Studies (Priority: P2)

An analyst wants to perform a statistical meta‑analysis that quantifies systematic agreement or bias between original and reproduced metrics across all surveyed papers.

**Why this priority**: The meta‑analysis turns per‑paper deviations into actionable scientific insight (e.g., whether discrepancies are random or systematic).

**Independent Test**: After reproducing metrics for at least three papers, invoke the statistical analysis module and verify that paired‑t‑tests, Bland‑Altman plots, and a mixed‑effects model are produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** reproduced and original metric vectors for *n* ≥ 3 papers, **when** the analysis module is executed, **then** it returns (a) paired‑t‑test p‑values for each metric, (b) Bland‑Altman plots saved as PNGs, and (c) a linear mixed‑effects summary reporting the influence of preprocessing choices, library versions, and seeds.

---

### User Story 3 – Generate Community Guidelines (Priority: P3)

A member of the synthetic‑chemistry community wants a concise checklist of best‑practice reproducibility recommendations derived from the study’s findings.

**Why this priority**: Translating empirical results into concrete guidance maximizes the project’s impact beyond the immediate reproducibility audit.

**Independent Test**: After the meta‑analysis finishes, run the guideline‑generation script and verify that a Markdown checklist containing at least five actionable items (e.g., “Report random seed”, “Version‑pin all libraries”, “Provide preprocessing scripts”) is produced.

**Acceptance Scenarios**:

1. **Given** the statistical summary of failure modes, **when** the guideline generator is invoked, **then** it outputs a Markdown document titled “Reproducibility Checklist for Reaction‑Yield Prediction” with numbered items and brief rationales.

---

### Edge Cases

- What happens when a target paper’s repository is unavailable or the code fails to compile on the CPU‑only environment?
- How does the system handle missing or ambiguous dataset split definitions (e.g., only a random‑split description without concrete indices)?
- What if the reported metrics use a different version of a library that changes default loss scaling, leading to systematic offsets?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest a CSV manifest of target papers (including DOI, repository URL, dataset name, and reported metrics) and validate that each entry contains the fields required for downstream processing. *(See US-1)*
- **FR-002**: The system MUST automatically construct a reproducible Docker image using Python 3.11, CPU‑only PyTorch 2.2, scikit‑learn 1.5, and RDKit, and must enforce that no GPU‑specific flags (e.g., `device_map="cuda"`) are used. *(See US-1)*
- **FR-003**: For each paper, the system MUST retrieve the exact dataset version (e.g., USPTO‑Extract v1.0) and any provided preprocessing scripts, and MUST verify that the dataset contains all variables required for the model (reactant/product SMILES, measured yield, and any covariates used in the original study). *(See US-1)*
- **FR-004**: The system MUST re‑implement or clone the model, set the random seed to the value reported (or to the default = 42 if not reported), and train/evaluate using the original hyper‑parameters and train/validation/test splits. *(See US-1)*
- **FR-005**: The system MUST compute the three primary metrics (MAE, R², Spearman ρ) on the held‑out test set and output a JSON record containing (a) reproduced values, (b) reported values, and (c) absolute deviations. *(See US-1)*
- **FR-006**: The system MUST perform paired statistical tests (paired t‑test) for each metric across all papers, apply a family‑wise error correction (Bonferroni), and flag any metric where the corrected p‑value < 0.05. *(See US-2)*
- **FR-007**: The system MUST generate Bland‑Altman plots for each metric and store them as PNG files named `{metric}_bland_altman.png`. *(See US-2)*
- **FR-008**: The system MUST fit a linear mixed‑effects model with random intercepts for paper and fixed effects for (i) preprocessing script version, (ii) library version, and (iii) random‑seed choice, reporting the variance explained by each factor. *(See US-2)*
- **FR-009**: The system MUST calculate a reproducibility score `S ∈ [0,1]` for each paper defined as `S = 1 – (|ΔMAE|/MAE_ref + |ΔR2|/|R2_ref| + |Δρ|/|ρ_ref|)/3`. *(See US-1)*
- **FR-010**: The system MUST run a sensitivity analysis sweeping the random seed over `{42, 123, 999}` and report the maximum metric variance observed; the analysis must be recorded in the final report. *(See US-1)*
- **FR-011**: The system MUST synthesize a Markdown checklist of at least five reproducibility best‑practice items derived from the failure‑mode analysis. *(See US-3)*
- **FR-012**: The system MUST log all environment details (Python version, library versions, OS, Docker image hash) to ensure traceability. *(Methodological soundness – dataset‑variable fit & inference framing)*

### Key Entities *(include if feature involves data)*

- **PaperManifest**: Represents a target publication; key attributes – DOI, repo URL, dataset identifier, reported metrics (MAE, R², ρ), hyper‑parameter dict, seed (optional).
- **ReproResult**: Holds reproduced metrics, deviations, reproducibility score, and any flags (missing seed, version mismatch).
- **StatSummary**: Contains outputs of paired tests, Bland‑Altman summaries, mixed‑effects coefficients, and multiple‑comparison correction results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For at least 70 % of papers, the absolute deviation of reproduced MAE from the reported value must be ≤ 0.02 yield‑units **and** the deviation of R² must be ≤ 0.02 (see US-1).
- **SC-002**: After Bonferroni correction, the paired t‑test must not reject the null hypothesis of no systematic bias for any metric at α = 0.05 (see US-2).
- **SC-003**: The sensitivity analysis (seed sweep) must show that the maximum standard deviation of any reproduced metric across the three seeds is ≤ 0.01 (see US-1).
- **SC-004**: The mixed‑effects model must explain ≥ 20 % of the variance in reproducibility scores with the fixed effects combined (see US-2).
- **SC-005**: The generated reproducibility checklist must contain at least five distinct, community‑vetted items and must be approved by at least two domain experts (simulated via a review step) (see US-3).

## Assumptions

- The USPTO‑Extract v1.0 dataset () includes all reaction‑specific variables required by the selected papers (reactant/product SMILES, measured yield). **The USPTO‑Extract v1.0 dataset provides core reaction data (reactant/product SMILES, measured yield) but temperature, solvent, and catalyst loading covariates are NOT guaranteed. Per community practice in reaction‑yield prediction (see USPTO‑Extract documentation and [J. Chem. Inf. Model. 2022, 62, 16, 3759–3771]), covariate availability is paper‑specific. The system MUST verify covariate presence per paper entry in the manifest (FR‑003) and flag any study that requires these covariates but cannot retrieve them, recording this as a known limitation in the results log.**
- All target papers provide either (i) a public repository with runnable code or (ii) a complete textual description that can be faithfully re‑implemented in ≤ 200 LOC of Python.
- Reported metrics are *associational* performance measures; the study will not claim causal inference about model superiority beyond reproducibility of reported numbers.
- The free‑tier GitHub Actions runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h wall‑time) is sufficient to train each model; models are limited to ≤ 1 M parameters or to classical ML algorithms (random forest, gradient boosting, shallow NN ≤ 3 layers).
- Library version differences are limited to major releases (e.g., scikit‑learn 1.4 → 1.5) that do not alter core metric implementations.
- The reproducibility score threshold of **0.8** for “high reproducibility” follows community practice in benchmark‑reproducibility studies (e.g., ImageNet reproducibility surveys).
- No GPU‑accelerated operations (e.g., `torch.cuda`, `bitsandbytes`) will be required; all code must run on CPU.
- The analysis will not attempt to retrain large transformer‑based models; if a paper’s model exceeds the 1 M‑parameter limit, it will be replaced by a published baseline of comparable architecture (recorded as a deviation in the results).

---
