# Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Schema-Test Mapping

| Schema File | Contract Test File | Schema Creation Phase | Test Execution Phase | Task ID |
|-------------|-------------------|----------------------|---------------------|----------|
| `specs/contracts/dataset.schema.yaml` | `code/tests/contract/test_dataset_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/anomaly_score.schema.yaml` | `code/tests/contract/test_anomaly_score_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/evaluation_metrics.schema.yaml` | `code/tests/contract/test_metrics_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/threshold_calibrator.schema.yaml` | `code/tests/contract/test_threshold_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/anomaly_detector.schema.yaml` | `code/tests/contract/test_anomaly_detector_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/dpgmm.schema.yaml` | `code/tests/contract/test_dp_gmm_schema.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/threshold_calibrator_service.schema.yaml` | `code/tests/contract/test_threshold_calibrator_service.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |
| `specs/contracts/anomaly_detector_service.schema.yaml` | `code/tests/contract/test_anomaly_detector_service.py` | Phase 8 (T184) | Phase 9 (T226) | T184, T226 |

**Total Contract Test Files**: 8 (6 schema tests + 2 service interface validation tests)

**Mapping Verification Task**: T226 verifies all eight contract tests are present and executable AFTER T184 completes. **T226 has explicit dependency on T184 in tasks.md Phase 9**.

**Schema Validation Task**: T185 validates all 8 schema files with YAML linter and stores validation logs in `code/tests/schema_validation_report.md` before contract test execution in Phase 9. **T185 is added to this mapping table for traceability**.

**Schema-Service Interface Validation Task**: T186 validates that the 8 schema YAML files match service interface method counts (AnomalyDetectorService=7, ThresholdCalibratorService=6) as defined in spec.md Service Interfaces section. **T186 is added to this mapping table for traceability**.

**Contract Test File Creation Schedule**:
- Phase 3 (T016): Creates 4 schema test FILES (dataset, anomaly_score, anomaly_detector, dpgmm) - test files reference schemas that will be created later
- Phase 4 (T025): Creates 1 schema test FILE (evaluation_metrics)
- Phase 5 (T034): Creates 1 schema test FILE (threshold_calibrator generic schema)
- Phase 6 (T162): Creates 2 service test FILES (anomaly_detector_service, threshold_calibrator_service)

**Note**: T016 creates 4 test FILES (dataset, anomaly_score, anomaly_detector, dpgmm schemas), T025 creates 1 (metrics), T034 creates 1 (threshold_calibrator generic schema), T162 creates 2 service test FILES. Total = 8 unique contract test FILES (4+1+1+2=8).

**Ordering Guarantee**: T226 is explicitly scheduled in Phase 9 AFTER T184 (Phase 8) completes. T184 must be marked [X] before T226 can be executed. **This ordering is enforced in tasks.md Phase 9 with explicit dependency declaration [DEPENDS: T016, T025, T034, T162, T184]**.

**Schema File Creation**: All 8 schema YAML files are created in Phase 8 (T184-T185) per spec.md Schema Definitions section. Contract test files are created in Phases 3-6 and validate schema compliance AFTER schemas are created in Phase 8. Schema files are validated in Phase 8 (T185) before contract tests in Phase 9 (T225-T228) can execute against them.

**Critical Distinction**: T016/T025/T034/T162 create CONTRACT TEST FILES (*.py) that validate schema compliance. T184 creates SCHEMA YAML FILES (*.yaml) that define the data contracts. Test files are created early but DO NOT validate schemas until schemas exist in Phase 8. Contract test execution in Phase 9 validates against Phase 8 schemas. This ordering eliminates the logical impossibility by separating test FILE creation from test EXECUTION.

**T150 Moved to Phase 9**: T150 (verify 8 contract test files executable) has been moved from Phase 7 to Phase 9 and consolidated into T225-T226 to ensure schemas exist before test execution verification.

**T223 External Verification Requirement**: T223 (re-run final_acceptance_verification.py) is added to plan.md Section 9.2 as an EXTERNAL VERIFICATION REQUIREMENT for T145 Final Acceptance. T145 cannot mark itself [X] until T223 shows exit code 0 in final_acceptance_report.md.

## 9.2 Deletion Traceability

**Phase 11 Deletion**: All original Phase 11 tasks (T237-T265) have been REDISTRIBUTED into Phase 2.5 and Phase 9 to eliminate logical contradictions and redundant task definitions. **New tasks T240-T250 in Phase 9.5/9.6 are ADDITIONAL filesystem verification tasks, NOT from original Phase 11**. This redistribution is documented in tasks.md Phase 10 footer and is tracked as a design decision in this section.

**T224 Deletion**: Task T224 (mark T145 as [X]) has been removed to eliminate circular dependency where T224 depended on T145 while T145 was the final acceptance gate. T145 now directly marks itself [X] after completing its own verification with external verification tasks (T222, T223, T226, T186) completing first. This deletion is documented in tasks.md Phase 10 footer and is tracked as a design decision in this section. **T145 Final Acceptance requires external verification evidence from T222 **(Phase 9 verification)

**Consolidation Decisions**:
- T160 removed - T037 is the single implementation task for ThresholdCalibratorService (Phase 5)
- T159 dependency on T037 removed - AnomalyDetectorService is independent per spec.md
- T023 and T177 consolidated - T177 creates directory, T023 logs to it
- T174 removed - T232-T236 are the verification tasks, T174 removed from dependency chain
- T153 and T214 consolidated - T214 is the verification task, T153 removed
- T165 consolidated into T163 - T163 now includes coverage verification

**Phase 9.5/9.6 Consolidation Rationale**: Phase 9.5/9.6 tasks (T240-T250) are NOT duplicates of Phase 2.5 and Phase 9 verification tasks (T210-T216). They provide EXPLICIT FILESYSTEM COMMAND EVIDENCE requirements that go beyond task completion markers. Phase 2.5 tasks perform the actual cleanup (T213, T216), while Phase 9.5 tasks provide VERIFICATION EVIDENCE (T240-T245) using explicit shell commands. This separation ensures auditability of filesystem hygiene.