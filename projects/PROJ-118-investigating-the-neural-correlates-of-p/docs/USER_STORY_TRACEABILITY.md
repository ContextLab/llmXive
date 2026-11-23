# User Story Traceability

This document maps project tasks to specific user stories and requirements.

## User Story 1: Preprocess Auditory Oddball EEG Data (P1)

**Goal**: Download, subsample, filter, epoch, and clean EEG data.

- **FR-001**: Data Acquisition (`code/download.py`, T010, T011)
- **FR-001b**: Channel Montage & Subsampling (`code/preprocess.py`, T015, T016)
- **FR-002**: Filtering & Re-referencing (`code/preprocess.py`, T017, T018)
- **FR-003**: ICA Artifact Removal (`code/preprocess.py`, T019, T020)
- **SC-001**: Rejection Rate Analysis (`code/analyze_rejection.py`, T021)
- **Integration**: T051 (Test `sub-01` pipeline)

## User Story 2: Extract MMN Amplitude and Latency Metrics (P2)

**Goal**: Calculate peak MMN amplitude and latency from difference waves.

- **FR-004**: ERP Computation & Difference Wave (`code/extract.py`, T022a, T022b)
- **FR-004**: Peak Search Logic (`code/extract.py`, T023)
- **SC-005**: Fallback Window & Flagging (`code/extract.py`, T024)
- **FR-004**: SNR Calculation (`code/extract.py`, T025)
- **FR-004**: Metrics CSV Generation (`code/extract.py`, T026)
- **Integration**: T050 (Test metric extraction)

## User Story 3: Statistical Comparison & Visualization (P3)

**Goal**: Perform stats and generate plots.

- **FR-005**: Data Filtering (`code/stats.py`, T029)
- **FR-005**: Paired T-Test (`code/stats.py`, T030)
- **FR-005**: FDR Correction (`code/stats.py`, T031)
- **SC-003 / Const-VII**: Mixed Effects Model (`code/stats.py`, T032)
- **FR-006**: Cluster-based Permutation (`code/stats.py`, T033)
- **SC-003**: Cohen's d (`code/stats.py`, T034)
- **FR-005**: Statistics JSON (`code/stats.py`, T035)
- **SC-001**: Prevalence Calculation (`code/viz.py`, T039)
- **SC-005**: Latency Validation (`code/stats.py`, T039b)
- **FR-007**: ERP Plots (`code/viz.py`, T036, T038)
- **FR-007**: Topographic Maps (`code/viz.py`, T037, T038)
- **Integration**: T051 (Stats test), T052 (Viz test)

## Cross-Cutting Concerns

- **T040**: Documentation (This document)
- **T002**: Dependencies
- **T005**: Configuration
