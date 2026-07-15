# Workflow Diagram

## High-Level Pipeline

```mermaid
graph TD
 A[Start] --> B[Phase 1: Setup]
 B --> C[Phase 2: Foundational]
 C --> D{Phase 3: US1 Data}
 D -->|Real EEG Found| E[T011: Preprocess Real EEG]
 D -->|Real EEG Not Found| F[T011b: Simulate EEG]
 E --> G[Phase 4: US2 Metrics]
 F --> G
 G --> H{Phase 5: US3 Stats}
 H --> I[T019: Correlation]
 I --> J[T020: Permutation Test]
 J --> K[T023: Report]
 K --> L{Phase 6: Revision}
 L --> M[T030-T033: Compliance]
 M --> N{Phase 7: Validation}
 N -->|N >= 10| O[T029a: Correlation Path]
 N -->|N < 10| P[T029b: Null Result Path]
 O --> Q[End]
 P --> Q
```

## Data Flow

```mermaid
graph LR
 Raw[dMRI + EEG Raw] -->|T009| Download[Downloaded Data]
 Download -->|T010| Connectome[Structural Connectome]
 Download -->|T011| RealEEG[Real EEG Time Series]
 Connectome -->|T011b| SimEEG[Simulated EEG Time Series]
 RealEEG -->|T015| Avalanches[Real Avalanches]
 SimEEG -->|T015b| SimAvalanches[Simulated Avalanches]
 Connectome -->|T014| Metrics[Network Metrics]
 Avalanches -->|T016| PowerLaw[Power-Law Fits]
 SimAvalanches -->|T016| SimPowerLaw[Sim Power-Law Fits]
 Metrics -->|T019| Stats[Correlation Results]
 PowerLaw -->|T019| Stats
 SimPowerLaw -->|T019| SimStats[Sim Correlation Results]
 Stats -->|T023| Report[Final Report]
```

## Component Interactions

- **T009** (Download) → **T010** (Preprocess dMRI)
- **T010** → **T011** (Real EEG) OR **T011b** (Sim EEG)
- **T011** → **T015** (Real Avalanches)
- **T011b** → **T015b** (Sim Avalanches)
- **T010** & **T015/T015b** → **T014** & **T016** (Metrics & Fitting)
- **T014** & **T016** → **T019** (Stats)
- **T019** → **T020** (Permutation) → **T023** (Report)
- **T023** → **T029a/T029b** (Validation)

## Parallel Execution Opportunities

- **Phase 1**: T001, T002, T003 (Setup)
- **Phase 2**: T004, T005, T006, T007, T008 (Foundational)
- **Phase 3**: T009, T010, T011, T011b (US1 - conditional paths)
- **Phase 4**: T014, T015, T015b, T016 (US2 - independent metric computation)
- **Phase 5**: T019, T020, T021, T022 (US3 - sequential dependencies)
