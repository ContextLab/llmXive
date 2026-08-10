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

- [ ] T005 [P] Implement data ingestion module `src/data/download_meg.py` using `datasets.load_dataset(..., streaming=True)` for OpenNeuro ds. **Deliverable**: `data/raw/meg_streamed.parquet`. **Verification**: `python -c "import pandas as pd; df=pd.read_parquet('data/raw/meg_streamed.parquet'); assert len(df)>1000"`. **Note**: Fail loudly if real data fetch fails; no synthetic fallback.
- [ ] T006 [P] Implement data ingestion module `src/data/download_clutrr.py` for Hugging Face `tasksource/clutrr`. **Deliverable**: `data/raw/clutrr.parquet`. **Verification**: `pytest tests/contract/test_clutrr_schema.py`. **Note**: Fail loudly if real data fetch fails; no synthetic fallback.
- [ ] T007-INGEST [P] Implement `src/data/preprocess_meg.py` (Part 1: Ingest): Load `meg_streamed.parquet` and extract `sensor_data` and `condition` fields. **Deliverable**: `data/processed/meg_raw.npy`. **Verification**: Output shape matches input rows. **Dependency**: T005.
- [ ] T007-FILTER [P] Implement `src/data/preprocess_meg.py` (Part 2: Filter): Bandpass filter `meg_raw.npy` (30-50Hz). **Deliverable**: `data/processed/meg_filtered.npy`. **Verification**: Output power in 30-50Hz band is non-zero. **Dependency**: T007-INGEST.
- [ ] T007-SNR-CALC [P] Implement `src/data/preprocess_meg.py` (Part 3: SNR): Calculate SNR for the 30-50Hz band in trials where `condition` matches 'binding' or 'gamma_binding'. **Deliverable**: `data/processed/meg_snr.json`. **Verification**: SNR value is a float. **Dependency**: T007-FILTER.
- [ ] T007-PSD [P] Implement `src/data/preprocess_meg.py` (Part 4: PSD): Compute Welch PSD with `nperseg=min(256, seq_len)`. **Note**: If `seq_len < 512`, zero-pad to 512 ONLY if unit tests (T016) confirm spectral peak integrity in 38-42Hz band is preserved. Normalize to unit area. **Deliverable**: `data/processed/meg_psd_normalized.npy`. **Verification**: Output matches `contracts/dataset.schema.yaml` spectral section. **Dependency**: T007-FILTER.
- [ ] T007-VALIDATE [P] Validate and store pre-processed MEG data. **Deliverable**: Validated `meg_psd_normalized.npy`. **Dependency**: T007-PSD.
- [ ] T009 [P] Create base model wrapper `src/models/base_model.py` loading DistilBERT in CPU-only mode. **Deliverable**: `src/models/base_model.py`. **Verification**: `python -c "from src.models.base_model import DistilBERTWrapper; print(DistilBERTWrapper)"`.
- [ ] T010 [P] Implement `src/analysis/stats.py` (Part 1): Permutation test engine (≥1000 iterations). **Deliverable**: `permute_test()` function in `src/analysis/stats.py`. **Implementation**: Must accept observed statistic, null distribution generator, and return p-value. **Verification**: `pytest tests/unit/test_stats.py`.
- [ ] T048 [P] Implement `src/analysis/stats.py` (Part 2): Bonferroni correction logic. **Deliverable**: `bonferroni_correct()` function. **Dependency**: T010.
- [ ] T012 [P] Implement `src/analysis/spectral.py`: FFT, Welch PSD, SNR calculation functions. **Note**: Uses output from T007. **Verification**: `pytest tests/unit/test_spectral.py`.
- [ ] T014 [P] Setup configuration management `config/default.yaml` for seeds, frequencies, and dataset paths. **Verification**: `python -c "import yaml; yaml.safe_load(open('config/default.yaml'))"`.
- [ ] T013-SDC [P] Implement `src/analysis/sdc.py`: Spectral Density Correlation (SDC) calculation (Pearson correlation of normalized PSDs). **Note**: SDC is the PRIMARY alignment metric per Plan revision (replacing PLV). **Deliverable**: `sdc_calc()` function in `src/analysis/sdc.py`. **Verification**: Output matches `contracts/output.schema.yaml` SDC section. **Dependency**: T012 (functions), T007 (data).

---

## Phase 2.5: Spec-Plan Reconciliation (Critical Traceability)

**Purpose**: Explicitly address Spec/Plan deviations to ensure traceability

- [ ] T003-PLV-REJECT [P] **Spec-Plan Reconciliation**: Implement a formal rejection protocol for FR-003/US-2 PLV requirement. **Deliverable**: `docs/traceability/plv_rejection_rationale.md` and `data/final/metric_definitions.json` (defining SDC as the primary metric). **Content Checklist**: 1. Cite FR-003, 2. Quote Plan.md rejection rationale ('Category Error'), 3. Define FR-003-SDC as replacement, 4. Verify SDC satisfies the *intent* of FR-003 (neural alignment) without violating the Plan. **Verification**: Reviewer confirms SDC is used in all subsequent tasks and PLV is explicitly absent. **Dependency**: T003-FR003-AMEND.
- [ ] T003-FR003-AMEND [P] **Spec Update**: Update `spec.md` to deprecate FR-003 (PLV) and replace it with FR-003-SDC. **Deliverable**: Updated `spec.md` with FR-003-SDC text. **Content**: 1. Cite FR-003, 2. State PLV rejection rationale, 3. Define FR-003-SDC as replacement, 4. Update spec.md text. **Verification**: `grep "FR-003-SDC" spec.md` returns non-empty. **Dependency**: None (runs early).

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
- [ ] T018-ORCHESTRATE [US1] Implement `src/main.py` orchestration: Load model, inject module (from T017) or use baseline, run forward pass, record `ActivationTimeSeries`. **Deliverable**: `src/main.py` with `--mode` flag (values: `oscillatory`, `baseline`). **Dependency**: T009, T017.
- [ ] T018-RUN-OSC [US1] Run `src/main.py` with `--mode oscillatory` to generate `ActivationTimeSeries` for oscillatory model. **Dependency**: T018-ORCHESTRATE.
- [ ] T018-RUN-BASE [US1] Run `src/main.py` with `--mode baseline` to generate `ActivationTimeSeries` for baseline model. **Dependency**: T018-ORCHESTRATE.
- [ ] T021 [US1] **Address Feynman/Krakauer**: Implement "Control Run" logic: Run same sequence with oscillation disabled to demonstrate feature integration failure. **Deliverable**: `data/final/control_runComparison.json` with schema: `{"oscillatory_coherence": float, "baseline_coherence": float, "coherence_difference": float, "is_significant": bool}`. **Note**: `is_significant` MUST be set to `True` if `coherence_difference >= 0.05`, else `False`. **Verification**: Validate output schema; ensure `is_significant` is calculated correctly. **Dependency**: T018-RUN-OSC, T018-RUN-BASE.
- [ ] T020 [US1] Implement SNR verification: Calculate peak power in target band vs. adjacent bands; assert SNR ≥ 3.0 dB. **Note**: Uses control run data from T021 for comparative verification. **Dependency**: T012, T018-RUN-OSC, T021.
- [ ] T019 [US1] Implement frequency sweep logic: Iterate relative frequencies across a range of cycle counts per sequence. **Deliverable**: `src/main.py` logic; Output artifact `data/processed/sweep_results.csv`. **Dependency**: T018-ORCHESTRATE.
- [ ] T022 [US1] **Address Rosalind Franklin**: Implement quantitative measurement protocol: Log spectral density, SDC values (from T013-SDC) across layers, and frequency stability metrics for every run. **Deliverable**: `data/processed/layer_metrics.csv` with columns: `[layer_id, head_id, frequency_stability, sdc_metric]`. **Dependency**: T012, T013-SDC, T018-RUN-OSC.
- [ ] T023 [US1] **Address Freeman Dyson**: Implement latency budget check: Measure forward pass time per batch; assert < 300s on CPU; log if > 300s. **Deliverable**: `data/final/latency_report.json`. **Dependency**: T018-ORCHESTRATE.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Neural Alignment with Human MEG/EEG Signatures (Priority: P2)

**Goal**: Compute Spectral Density Correlation (SDC) between model activations and OpenNeuro MEG reference.

**Independent Test**: Compute SDC between model and MEG data; verify significant correlation (p < 0.05) via permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US2] Contract test for `SpectralFeatures` schema in `tests/contract/test_spectral_features.py`
- [ ] T025 [P] [US2] Integration test for SDC calculation against known synthetic signal in `tests/integration/test_sdc_calc.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/data/preprocess_meg.py` fallback: If specific binding condition (trials with `condition` == 'binding' or 'gamma_binding') SNR < 2.0, switch to broader gamma response (30-50Hz). **Deliverable**: `data/processed/meg_fallback.npy`. **Dependency**: Requires SNR metric from T007-SNR-CALC.
- [ ] T027 [US2] Implement `src/analysis/sdc.py` integration: Compare model `ActivationTimeSeries` (from T018-RUN-OSC) PSD and SDC with pre-processed MEG PSD and SDC (from T007, T013-SDC). Calculate the difference in SDC between oscillatory and baseline models. **Deliverable**: `data/final/sdc_comparison.json`. **Verification**: Report SDC difference; if > 0.15, flag as significant; otherwise report actual value. **Dependency**: T013-SDC, T007, T018-RUN-OSC, T018-RUN-BASE.
- [ ] T027b [US2] Implement permutation test wrapper for SDC difference: Shuffle model/MEG labels multiple times to generate null distribution for SDC difference metric. **Deliverable**: `src/analysis/stats.py` wrapper; Output artifact `data/final/permutation_results_sdc.json`. **Dependency**: T010, T027.
- [ ] T030 [US2] **Address Kandel**: Implement "Stability Check": Run inference on the same sequence after oscillation removal; verify if the "binding" effect (SDC) remains stable or decays. **Deliverable**: `data/final/stability_check_results.json` with schema: `{"stability_score": float, "decay_observed": bool}`. **Note**: Replaces 'Persistence Check' with stability verification. **Dependency**: T018-RUN-OSC, T018-RUN-BASE, T013-SDC.
- [ ] T031 [US2] Implement output labeling: Explicitly label all similarity scores as "Associational Similarity Score" in `data/final/statistical_report.json`. **Deliverable**: `src/analysis/reporting.py`. **Dependency**: T048.
- [ ] T032 [US2] **Address Rosalind Franklin**: Implement frequency bandwidth analysis: Report the bandwidth around the dominant frequency where SDC remains significant.; log phase coherence scaling with sequence length. **Dependency**: T019, T027.

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
- [ ] T039-SYNTH [US3] **Address Feynman**: Create minimal synthetic case for binding visualization. **Deliverable**: `data/synthetic/color_motion.json` (minimal graph structure with defined features). **Note**: This task generates the input artifact required for T040. **Warning**: This synthetic data is ONLY for visualization and T040; it MUST NOT be used for SDC/PLV calculations against MEG data. **Dependency**: None.
- [ ] T040 [US3] **Address Feynman**: Implement "Toy Failure" demonstration: Compare baseline vs oscillatory model on the synthetic dataset from T039-SYNTH. **Deliverables**: `data/final/toy_failure_results.json` with schema: `{"baseline_accuracy": float, "oscillatory_accuracy": float}`. **Note**: Run comparison and report results; analyze if oscillatory model shows improvement. **Dependency**: T018-RUN-OSC, T018-RUN-BASE, T039-SYNTH.
- [ ] T039 [US3] **Address Krakauer**: Implement "Correlation vs. Binding" test: Compare performance on tasks requiring feature integration vs. simple feature extraction. **Deliverable**: `data/final/binding_vs_extraction_comparison.csv` with columns: `[task_type, accuracy, f1_score]`. **Statistical Test**: Paired t-test on accuracy between 'integration' and 'extraction' types. **Note**: Removed specific taxonomy requirement; use existing task metadata. **Dependency**: Requires `task_classification.json` from T035, T036.
- [ ] T037 [US3] Implement statistical aggregation: Run multiple seeds for both models. **Deliverable**: `data/final/aggregated_results.json`. **Dependency**: T035, T036.
- [ ] T038 [US3] Implement global Bonferroni correction: Apply correction across ALL statistical tests performed in frequency sweeps AND benchmark tasks (global family-wise error rate control). **Deliverable**: `data/final/bonferroni_corrected_results.json`. **Dependency**: T048.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates: Add "Mapping Hypothesis" section to `README.md` explaining relative frequency vs. physical time
- [ ] T042 [P] **Address von Neumann**: Implement feature definition schema validation. **Deliverable**: `data/final/feature_definition_schema.json`. **Dependency**: T041 (if T041 is renumbered), T051 (old ID). **Note**: This task validates the schema generated in T040. **Dependency**: T040.
- [ ] T043 Code cleanup: Ensure all random seeds are pinned and logged in `data/final/statistical_report.json`
- [ ] T044 [P] Performance optimization: Verify streaming logic prevents OOM on constrained-memory runner. **Verification**: Run on a constrained RAM limit and log success.
- [ ] T045 [P] Additional unit tests: `tests/unit/test_sdc.py`, `tests/unit/test_stats.py`
- [ ] T046 Security hardening: Verify no PII in MEG data (confirm OpenNeuro anonymization)
- [ ] T047 Run `quickstart.md` validation: Ensure all commands execute successfully. **Deliverable**: `data/validation_log.txt`.
- [ ] T053 [P] **Address All Reviewers**: Compile a "Limitations & Falsification" section in `research.md` explicitly stating where the model fails to bind, where the oscillation is merely correlational, and the specific conditions under which the 40Hz hypothesis is rejected. **Deliverable**: Updated `research.md` with a dedicated "Falsification Evidence" subsection.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 2.5 (Reconciliation)**: Depends on Foundational completion
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
3. Complete Phase 2.5: Reconciliation
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify spectral peak)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 2.5 (Reconciliation) → Traceability locked
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **Critical**: MEG comparison is "Spectral Density Correlation (SDC)" (Primary) and "PLV" (Removed per Plan).
- **Critical**: Bonferroni correction applied globally across all families (FR-006).
- **Critical Reviewer Addressing**:
 - **Krakauer**: Differentiating correlation vs. causal binding via T021, T039, T040.
 - **Kandel**: Addressing "what remains" via T030 (Stability Check).
 - **Dyson**: Latency budget check via T023.
 - **Feynman**: Physical mechanism visualization and toy failure via T040.
 - **Franklin**: Quantitative constraints, bandwidth, and falsification via T022, T032, T053.