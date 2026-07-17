# Implementation Plan: Predicting Elastic Moduli of 2D Materials

## Phase 1: Setup (Shared Infrastructure)
- [X] T001a: Update terminology to "Structure-Only Surrogate Model"
- [X] T002: Initialize Python 3.11 project with pinned dependencies
- [X] T003: Configure linting (ruff) and formatting (black)

## Phase 2: Foundational (Blocking Prerequisites)
- [X] T004: Environment configuration (seeding, paths)
- [X] T005: Logging infrastructure
- [X] T006: Constants and unit conversions
- [X] T007: `MaterialGraph` data schema
- [X] T008: Dynamic sampling strategy (7GB limit)

## Phase 3: User Story 1 - Data Ingestion (P1)
- [X] T009: Unified dataset loader
- [X] T010: CIF parser
- [X] T011: 2D filter and tensor validator
- [X] T012: Bias check for exclusions
- [X] T013: Pipeline orchestration
- [X] T014: Unit tests for parsing
- [X] T015: Unit tests for filtering

## Phase 4: User Story 2 - GNN Training (P2)
- [X] T016: Lightweight GNN architecture
- [X] T017: Stratified splitting logic
- [X] T018: Training loop with early stopping
- [X] T019: Evaluation and metrics
- [X] T020: K-fold cross-validation
- [X] T020a: Intra-family baseline
- [X] T021: Inter-family generalization test
- [X] T022: Integration test

## Phase 5: User Story 3 - Feature Importance (P3)
- [X] T023: SHAP value calculation
- [X] T024: Permutation importance
- [X] T025: Composition-only baseline
- [X] T026: Ablation study runner
- [X] T027: Final analysis report
- [X] T028: Unit tests for importance

## Execution Strategy
1. Complete Setup and Foundational phases first.
2. Implement US1 to establish data pipeline.
3. Implement US2 for model training.
4. Implement US3 for analysis.
5. Validate each user story independently before proceeding.

## Risk Mitigation
- **Memory**: Use `dynamic_sampling` in T008 to enforce 7GB limit.
- **Data Quality**: Strict filtering in T011 and bias checks in T012.
- **Generalization**: Stratified splitting in T017 and inter-family testing in T021.
