# Implementation Plan: The Impact of Visual Attention on False Memory Formation

## Executive Summary
This project investigates the relationship between visual attention (saliency) and false memory formation using the Visual Genome dataset and recall transcripts. We will compute object-level saliency scores and correlate them with false memory rates.

## Research Question
Do objects that attract higher visual attention (saliency) have higher rates of false memory formation?

## Hypothesis
H1: There is a positive correlation between object saliency scores and false memory rates.

## Methodology
1. **Data Sources**:
 - Visual Genome (VG) for images and object annotations
 - SALICON for saliency model validation
 - Recall transcripts from prior studies (linked via VG IDs)

2. **Pipeline**:
 - Download and preprocess VG and SALICON datasets
 - Compute saliency maps using a pre-trained model (CPU-compatible)
 - Link VG image IDs with recall transcripts
 - Filter for false memory candidates
 - Calculate correlation between saliency and false memory rates
 - Perform robustness checks and noise analysis

3. **Analysis**:
 - Pearson correlation coefficient (r, p, CI)
 - Mixed-effects logistic regression
 - Benjamini-Hochberg FDR correction
 - Sensitivity analysis across thresholds

## Constitution Check
**Status: PASS**
- T008a: Visual Genome URL verified and documented in `data/verified_sources.md`
- T008b: SALICON URL verified and documented in `data/verified_sources.md`
- All foundational prerequisites (T001-T007) are complete.
- Data sources are accessible and valid for the study.

## Constraints
- CPU-only execution (no GPU, no 8-bit/4-bit quantization)
- Maximum 224x224 image downsampling for saliency computation
- Alpha = 0.01, Power = 0.80 for sample size calculation
- Study invalidation if noise correlation > threshold (configurable)
- Ethics gate: IRB approval must be present in `data/ethics/`

## Deliverables
- `data/processed/saliency_scores.json`: Object-level saliency scores
- `data/processed/correlation_results.json`: Pearson correlation and regression results
- `data/processed/robustness_report.md`: Sensitivity analysis report
- `data/processed/study_status.json`: Final validity status

## Timeline
- Phase 1: Setup (Complete)
- Phase 2: Foundational (Complete)
- Phase 3: User Story 1 (In Progress)
- Phase 4: User Story 2 (Pending)
- Phase 5: User Story 3 (Pending)
- Phase 6: Validity & Noise Checks (Pending)
- Phase N: Polish & Cross-Cutting Concerns (Pending)
