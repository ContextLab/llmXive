# Tasks: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`)
- [X] T002 Initialize Python 3.11 project with `transformers`, `torch`, `scipy`, `mne`, `datasets` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `.pre-commit-config.yaml`
- [X] T004 [P] Setup `pytest` configuration in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement data ingestion module `src/data/download_meg.py` using `datasets.load_dataset(..., streaming=True)` for OpenNeuro ds000246. **Deliverable**: `data/raw/meg_streamed.parquet`. **Verification**: `python -c "import pandas as pd; df=pd.read_parquet('data/raw/meg_streamed.parquet'); assert len(df)>1000"`.
- [ ] T006 Implement data ingestion module `src/data/download_clutrr.py` for Hugging Face `tasksource/clutrr`. **Deliverable**: `data/raw/clutrr.parquet`. **Verification**: `pytest tests/contract/test_clutrr_schema.py`.
- [ ] T007 [P] Implement `src/data/preprocess_meg.py` (Part 1): Bandpass filter 30-50Hz on streamed MEG data. [UNRESOLVED-CLAIM: c_6469b9cc — status=not_enough_info] **Deliverable**: `data/processed/meg_filtered.npy`. **Dependency**: None.
- [ ] T047 Implement `src/data/preprocess_meg.py` (Part 2): Compute Welch PSD (zero-pad to 512 if seq_len < 512) and normalize to unit area. [UNRESOLVED-CLAIM: c_d5e71987 — status=not_enough_info] **Deliverable**: `data/processed/meg_psd_normalized.npy`. **Verification**: Output matches `contracts/dataset.schema.yaml` spectral section. **Dependency**: T007.
- [X] T008 [P] Implement `src/data/preprocess_meg.py` (Part 3): Validate and store pre-processed MEG data. **Deliverable**: Validated `meg_psd_normalized.npy`. **Dependency**: T047.
- [ ] T009 [P] Create base model wrapper `src/models/base_model.py` loading DistilBERT in CPU-only mode. **Deliverable**: `src/models/base_model.py`. **Verification**: `python -c "from src.models.base_model import DistilBERTWrapper; print(DistilBERTWrapper)"`.
- [X] T010 [P] Implement `src/analysis/stats.py` (Part 1): Permutation test engine (≥1000 iterations). [UNRESOLVED-CLAIM: c_6a3445b3 — status=not_enough_info] **Deliverable**: `permute_test()` function in `src/analysis/stats.py`. **Verification**: `pytest tests/unit/test_stats.py`.
- [X] T048 [P] Implement `src/analysis/stats.py` (Part 2): Bonferroni correction logic. **Deliverable**: `bonferroni_correct()` function. **Dependency**: T010.
- [ ] T012 [P] Implement `src/analysis/spectral.py`: FFT, Welch PSD, SNR calculation functions. **Note**: Uses output from T047. **Verification**: `pytest tests/unit/test_spectral.py`.
- [ ] T013 [P] Implement `src/analysis/sdc.py`: Spectral Density Correlation (SDC) calculation (Pearson correlation of normalized PSDs). **Note**: SDC is a complementary/secondary metric to PLV for methodological rigor regarding discrete/continuous time comparison. **Verification**: Output matches `contracts/output.schema.yaml` SDC section. **Dependency**: T012, T047.
- [ ] T013b [P] Implement `src/analysis/plv.py`: Phase Locking Value (PLV) calculation as mandated by FR-003. **Deliverable**: `plv_calc()` function in `src/analysis/plv.py`. **Verification**: `pytest tests/unit/test_plv.py`. **Note**: Primary metric per spec; SDC is secondary.
- [X] T014 [P] Setup configuration management `config/default.yaml` for seeds, frequencies, and dataset paths. **Verification**: `python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement CPU-Tractable Oscillatory Attention Mechanism (Priority: P1) 🎯 MVP

**Goal**: Inject phase-locked sinusoidal gating into DistilBERT attention heads and verify spectral peak presence.

**Independent Test**: Run a forward pass on a batch of sequences of tokens; verify FFT shows a peak in the target band with SNR ≥ 3.0 dB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Contract test for `ActivationTimeSeries` schema in `tests/contract/test_activation_schema.py`
- [X] T016 [P] [US1] Integration test for spectral peak detection in `tests/integration/test_oscillation_peak.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement `OscillatoryAttentionModule` in `src/models/oscillatory_attention.py`: Inject sinusoidal mask at relative frequency `f` (cycles/sequence). **Deliverable**: Module class ready for injection.
- [X] T018 [US1] Implement `src/main.py` orchestration: Load model, inject module (from T017), run forward pass, record `ActivationTimeSeries`. **Dependency**: T009, T017.
- [X] T018b [US1] Implement `src/main.py` baseline run: Load model without oscillatory module, run forward pass, record `ActivationTimeSeries` for control comparison. **Dependency**: T009.
- [ ] T021 [US1] **Address Feynman/Krakauer**: Implement "Control Run" logic: Run same sequence with oscillation disabled to demonstrate feature integration failure. **Deliverable**: `data/final/control_run_comparison.json` with schema: `{"oscillatory_coherence": float, "baseline_coherence": float, "coherence_difference": float}`. **Note**: Report difference descriptively; no hard threshold assertion. **Dependency**: T018, T018b.
- [ ] T020 [US1] Implement SNR verification: Calculate peak power in target band vs. adjacent bands; assert SNR ≥ 3.0 dB. **Note**: Uses control run data from T021 for comparative verification. **Dependency**: T012, T018.
- [ ] T019 [US1] Implement frequency sweep logic: Iterate relative frequencies across a range of cycle counts per sequence. **Deliverable**: `src/main.py` logic; Output artifact `data/processed/sweep_results.csv`. **Dependency**: T018.
- [ ] T022 [US1] **Address Rosalind Franklin**: Implement quantitative measurement protocol: Log spectral density, phase-locking values (from T013b) across layers, and frequency stability metrics for every run. **Deliverable**: `data/processed/layer_metrics.csv` with columns: `[layer_id, head_id, frequency_stability, phase_locking_metric]`. **Dependency**: T012, T013b, T018, T019.
- [ ] T023 [US1] **Address Freeman Dyson**: Implement latency budget check: Measure forward pass time per batch; assert < 300s on CPU; log if > 25ms/token equivalent. **Deliverable**: `data/final/latency_report.json`. **Dependency**: T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Neural Alignment with Human MEG/EEG Signatures (Priority: P2)

**Goal**: Compute Phase Locking Value (PLV) and Spectral Density Correlation (SDC) between model activations and OpenNeuro MEG reference.

**Independent Test**: Compute PLV between model and MEG data; verify significant correlation (p < 0.05) via permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US2] Contract test for `SpectralFeatures` schema in `tests/contract/test_spectral_features.py`
- [ ] T025 [P] [US2] Integration test for PLV calculation against known synthetic signal in `tests/integration/test_plv_calc.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/data/preprocess_meg.py` fallback: If specific "binding" condition SNR < 2.0, switch to broader 30-50Hz gamma response. **Deliverable**: `data/processed/meg_fallback.npy`. **Dependency**: Requires SNR metric from T047.
- [ ] T027 [US2] Implement `src/analysis/sdc.py` and `src/analysis/plv.py` integration: Compare model `ActivationTimeSeries` (from T018) PSD and PLV with pre-processed MEG PSD and PLV (from T047, T013b). **Dependency**: T013, T013b, T047, T018.
- [ ] T028 [US2] Implement permutation test wrapper: Shuffle model/MEG labels multiple times to generate null distribution. **Deliverable**: `src/analysis/stats.py` wrapper; Output artifact `data/final/permutation_results.json`. **Dependency**: T010.
- [ ] T029 [US2] **Address von Neumann**: Implement explicit "Feature" definition: Map attention heads to feature groups; log which heads are bound by the oscillation. **Deliverable**: `data/final/bound_heads_mapping.json` with schema: `{"layer_head_id": "bound_group_id",...}`.
- [ ] T030 [US2] **Address Kandel**: Implement "Stability Check": Run inference on the same sequence after oscillation removal; verify if the "binding" effect (PLV/SDC) remains stable or decays. **Deliverable**: `data/final/stability_check_results.json` with schema: `{"stability_score": float, "decay_observed": bool}`. **Note**: Replaces 'Persistence Check' with stability verification. **Dependency**: T018, T018b.
- [ ] T031 [US2] Implement output labeling: Explicitly label all similarity scores as "Associational Similarity Score" in `data/final/statistical_report.json`. **Deliverable**: `src/analysis/reporting.py`. **Dependency**: T048.
- [ ] T032 [US2] **Address Rosalind Franklin**: Implement frequency bandwidth analysis: Report the bandwidth around 40Hz where SDC/PLV remains significant; log phase coherence scaling with sequence length. **Dependency**: T019, T027.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate Compositional Reasoning Performance (Priority: P3)

**Goal**: Evaluate oscillatory model on CLUTRR/bAbI benchmarks and compare to baseline.

**Independent Test**: Run CLUTRR (a set of samples, multi-hop) across multiple seeds; report accuracy/F1 and paired t-test results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Contract test for `BenchmarkResult` schema in `tests/contract/test_benchmark_schema.py`
- [ ] T034 [P] [US3] Integration test for CLUTRR evaluation pipeline in `tests/integration/test_clutrr_eval.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] Implement `src/benchmarks/clutrr_eval.py`: Load dataset, run inference, compute accuracy/F1. **Deliverable**: `data/processed/task_classification.json` (metadata distinguishing 'integration' vs 'extraction' tasks).
- [ ] T036 [US3] Implement `src/benchmarks/babi_eval.py`: Load dataset, run inference, compute accuracy/F1. **Deliverable**: `data/processed/task_classification.json` (metadata distinguishing 'integration' vs 'extraction' tasks).
- [ ] T037 [US3] Implement statistical aggregation: Run multiple seeds for both models. **Deliverable**: `data/final/aggregated_results.json`. **Dependency**: T035, T036.
- [ ] T038 [US3] Implement Bonferroni correction: Apply correction *within* the frequency sweep family and *within* the benchmark family separately (not across the combined set of multiple comparisons). **Deliverable**: `data/final/bonferroni_corrected_results.json`. **Dependency**: T048.
- [ ] T039 [US3] **Address Krakauer**: Implement "Correlation vs. Binding" test: Compare performance on tasks requiring feature integration vs. simple feature extraction. **Deliverable**: `data/final/binding_vs_extraction_comparison.csv` with columns: `[task_type, accuracy, f1_score]`. **Statistical Test**: Paired t-test on accuracy between 'integration' and 'extraction' types. **Note**: Removed specific taxonomy requirement; use existing task metadata. **Dependency**: Requires `task_classification.json` from T035/T036.
- [ ] T040 [US3] **Address Feynman**: Implement "Toy Failure" demonstration: Create a minimal synthetic case where oscillation is required to solve the task; verify baseline fails. **Deliverables**: `data/synthetic/toy_failure_case.json` (minimal graph structure) and `data/final/toy_failure_results.json` with schema: `{"baseline_accuracy": float, "oscillatory_accuracy": float}`. **Assertion**: `baseline_accuracy < 0.5` and `oscillatory_accuracy > 0.5`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates: Add "Mapping Hypothesis" section to `README.md` explaining relative frequency vs. physical time
- [ ] T042 Code cleanup: Ensure all random seeds are pinned and logged in `data/final/statistical_report.json`
- [ ] T043 Performance optimization: Verify streaming logic prevents OOM on constrained-memory runner. [UNRESOLVED-CLAIM: c_706e7872 — status=not_enough_info] **Verification**: Run on 7GB RAM limit and log success.
- [ ] T044 [P] Additional unit tests: `tests/unit/test_sdc.py`, `tests/unit/test_stats.py`
- [ ] T045 Security hardening: Verify no PII in MEG data (confirm OpenNeuro anonymization)
- [ ] T046 Run `quickstart.md` validation: Ensure all commands execute successfully. **Deliverable**: `data/validation_log.txt`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for `ActivationTimeSeries` data (T018)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for ActivationTimeSeries schema in tests/contract/test_activation_schema.py"
Task: "Integration test for spectral peak detection in tests/integration/test_oscillation_peak.py"

# Launch all models for User Story 1 together:
Task: "Implement OscillatoryAttentionModule in src/models/oscillatory_attention.py"
Task: "Implement frequency sweep logic in src/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify spectral peak)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Oscillatory Mechanism)
 - Developer B: User Story 2 (MEG Alignment)
 - Developer C: User Story 3 (Benchmarks)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data loading MUST fail loudly on missing real data; no synthetic fallbacks.
- **Critical**: Frequency is defined as "cycles per sequence length", not physical Hz.
- **Critical**: MEG comparison is "Phase Locking Value (PLV)" (primary) and "Spectral Density Correlation (SDC)" (secondary).
- **Critical**: Bonferroni correction applied within families, not across all comparisons.