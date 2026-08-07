# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 45 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T021b-ValidateDesign is listed as running 'after T013'. T013 is in Phase 2 (US1). T021b is in Phase 3 (US2). This is correct. However, T021c-GenerateConfig is listed as running 'after T021b, T014a, and T014c-FlagAmbiguousType'. T014a is in Phase 1. T021c (Phase 3) depends on T014a (Phase 1). This is a valid cross-phase dependency, but T014a's placement in Phase 1 is problematic as it depends on T013 (Phase 2). The chain T013 -> T014a -> T021c is broken because T014a is in Phase 1. T014a must be moved to Phase 2.
- T023b-SimulationValidation is marked [P] (Parallel) but its description states: 'This task requires the injected parameter from `simulation_parameters.json` (T000h-SimulateParams) and the model output from T023. It is NOT parallelizable with T023.' The [P] tag is explicitly contradicted by the task description. This is a semantic violation of the [P] correctness rule.
- T025a and T025b (Contract tests) are marked [P] and listed in Phase 3. T025a depends on T024b-SchemaDef (Phase 1) and T021c-GenerateConfig (Phase 3). T025b depends on T020b (Phase 1). While tests can be written in parallel, the task descriptions imply they validate the *output* of T021c and T023. If T021c and T023 are not yet run, these tests cannot execute. The [P] tag is acceptable for *writing* the tests, but the dependency on T021c (which is in the same phase) suggests a sequential execution flow for the *validation* step. This is a minor semantic issue, but the [P] tag is technically correct for the *implementation* of the test file.
- T030 (Sensitivity Analysis) is listed as running 'after T013 and T000h-SimulateParams'. T013 is in Phase 2. T000h is in Phase 0. This is correct. However, T030's description says: 'Calculate absolute deviation from the *cell mean*... using the *per-cell standard deviation*'. This requires the data to be cleaned and binned (T012a, T012b, T013). T030 depends on T013, which is in Phase 2. T030 is in Phase 4. This is a valid cross-phase dependency. No violation here.
- T033 (Report Generation) is listed as running 'after T035-ReportSchema, T032, T030, T023, and T022'. T023 and T022 are in Phase 3. T030 is in Phase 4. T033 is in Phase 4. This is correct. However, T033 depends on T023 (model output) and T030 (sensitivity output). T023 is in Phase 3, T030 is in Phase 4. This implies T033 must wait for Phase 4 tasks to complete. This is a valid dependency chain.
- T010a (Read simulation params) is listed as running 'after T000h-SimulateParams'. T000h is in Phase 0. T010a is in Phase 1. This is correct. However, T010b (Execute Data Source) is listed as running 'after T010a, T010i-CreateRegistrySchema, and T000h-SimulateParams'. T010i is in Phase 1. T010b is in Phase 1. This is correct. But T010b depends on T010i (Create Registry Schema). T010i is a schema definition task. T010b is a data execution task. This is a valid producer-consumer relationship.
- T010d-Merge is listed as running 'after T010b-ExecuteDataSource'. T010b produces the active data source. T010d merges it. This is correct. However, T010d is in Phase 1, while T010b is in Phase 1. This is correct. But T010d depends on T010b, which is in the same phase. This is a valid sequential dependency within Phase 1.
- T011 (Validate variance) is listed as running 'after T010d-Merge'. T010d produces `cleaned_data.csv`. T011 validates it. This is correct. However, T011 is in Phase 2, while T010d is in Phase 1. This is a valid cross-phase dependency.
- T012a (Map factors) is listed as running 'after T011'. T011 validates variance. T012a maps factors. This is correct. However, T012a is in Phase 2, while T011 is in Phase 2. This is a valid sequential dependency within Phase 2.
- T012c-FlagAmbiguity is listed as running 'after T012b'. T012b bins. T012c flags ambiguity. This is correct. However, T012c is in Phase 2, while T012b is in Phase 2. This is a valid sequential dependency within Phase 2.
- T014a (Detect outcome type) is listed as running 'after T013'. T013 is in Phase 2. T014a is in Phase 1. This is a violation: a Phase 1 task depends on a Phase 2 task. T014a must be moved to Phase 2.
- T014b (Review preprocess) is listed as running 'after T014a'. T014a is in Phase 1. T014b is in Phase 2. This is a valid cross-phase dependency, but T014a's placement in Phase 1 is problematic.
- T015 (Contract test) is listed as running 'after T014b'. T014b is in Phase 2. T015 is in Phase 2. This is a valid sequential dependency within Phase 2.
- T016 (Unit test) is listed as running 'after T015'. T015 is in Phase 2. T016 is in Phase 2. This is a valid sequential dependency within Phase 2.
- T021b-ValidateDesign is listed as running 'after T013'. T013 is in Phase 2. T021b is in Phase 3. This is a valid cross-phase dependency.
- T014c-FlagAmbiguousType is listed as running 'after T014a'. T014a is in Phase 1. T014c is in Phase 3. This is a valid cross-phase dependency, but T014a's placement in Phase 1 is problematic.
- T021c-GenerateConfig is listed as running 'after T021b, T014a, and T014c-FlagAmbiguousType'. T021b is in Phase 3. T014a is in Phase 1. T014c is in Phase 3. T021c is in Phase 3. This is a valid cross-phase dependency, but T014a's placement in Phase 1 is problematic.
- T021a (Fit model) is listed as running 'after T021c-GenerateConfig'. T021c is in Phase 3. T021a is in Phase 3. This is a valid sequential dependency within Phase 3.
- T022 (Calculate VIF) is listed as running 'after T021a'. T021a is in Phase 3. T022 is in Phase 3. This is a valid sequential dependency within Phase 3.
- T023 (Extract coefficients) is listed as running 'after T022'. T022 is in Phase 3. T023 is in Phase 3. This is a valid sequential dependency within Phase 3.
- T023c-ValidateCIWidth is listed as running 'after T023'. T023 is in Phase 3. T023c is in Phase 3. This is a valid sequential dependency within Phase 3.
- T024 (Fallback logic) is listed as running 'after T023'. T023 is in Phase 3. T024 is in Phase 3. This is a valid sequential dependency within Phase 3.
- T025a (Contract test) is listed as running 'after T024b-SchemaDef and T021c-GenerateConfig'. T024b is in Phase 1. T021c is in Phase 3. T025a is in Phase 3. This is a valid cross-phase dependency.
- T025b (Contract test) is listed as running 'after T020b'. T020b is in Phase 1. T025b is in Phase 3. This is a valid cross-phase dependency.
- T026 (Unit test) is listed as running 'after T025b'. T025b is in Phase 3. T026 is in Phase 3. This is a valid sequential dependency within Phase 3.
- T030 (Sensitivity Analysis) is listed as running 'after T013 and T000h-SimulateParams'. T013 is in Phase 2. T000h is in Phase 0. T030 is in Phase 4. This is a valid cross-phase dependency.
- T031 (Post-hoc comparisons) is listed as running 'after T030'. T030 is in Phase 4. T031 is in Phase 4. This is a valid sequential dependency within Phase 4.
- T031b-ValidateStability is listed as running 'after T030'. T030 is in Phase 4. T031b is in Phase 4. This is a valid sequential dependency within Phase 4.
- T035-ReportSchema is listed as running 'before T033'. T033 is in Phase 4. T035 is in Phase 4. This is a valid sequential dependency within Phase 4.
- T032 (Forest plot) is listed as running 'after T030'. T030 is in Phase 4. T032 is in Phase 4. This is a valid sequential dependency within Phase 4.
- T032b (Template) is listed as running 'after T030'. T030 is in Phase 4. T032b is in Phase 4. This is a valid sequential dependency within Phase 4.
- T033 (Report Generation) is listed as running 'after T035-ReportSchema, T032, T030, T023, and T022'. T035 is in Phase 4. T032 is in Phase 4. T030 is in Phase 4. T023 is in Phase 3. T022 is in Phase 3. T033 is in Phase 4. This is a valid cross-phase dependency.
- T036-ReportValidation is listed as running 'after T033'. T033 is in Phase 4. T036 is in Phase 4. This is a valid sequential dependency within Phase 4.
- T043a (Unit test) is listed as running 'after T030'. T030 is in Phase 4. T043a is in Phase 4. This is a valid sequential dependency within Phase 4.
- T043b (Unit test) is listed as running 'after T022'. T022 is in Phase 3. T043b is in Phase 4. This is a valid cross-phase dependency.
- T040b (Add docstrings) is listed as running 'after T040a'. T040a is in Phase N. T040b is in Phase N. This is a valid sequential dependency within Phase N.
- T041a-Analysis (Refactor) is listed as running 'after T040b'. T040b is in Phase N. T041a is in Phase N. This is a valid sequential dependency within Phase N.
- T041b-Simulate (Refactor) is listed as running 'after T041a-Analysis'. T041a is in Phase N. T041b is in Phase N. This is a valid sequential dependency within Phase N.
- T042a-Baseline (Profile) is listed as running 'after T041b-Simulate'. T041b is in Phase N. T042a is in Phase N. This is a valid sequential dependency within Phase N.
- T042b-PerformanceCheck is listed as running 'after T042a-Baseline'. T042a is in Phase N. T042b is in Phase N. This is a valid sequential dependency within Phase N.
- T053 (Data Integrity) is listed as running 'after T053a-DefineExceptions'. T053a is in Revision Concerns. T053 is in Revision Concerns. This is a valid sequential dependency within Revision Concerns.
- T054 (Parameter Drift) is listed as running 'after T053'. T053 is in Revision Concerns. T054 is in Revision Concerns. This is a valid sequential dependency within Revision Concerns.
- T055 (Edge Case) is listed as running 'after T054'. T054 is in Revision Concerns. T055 is in Revision Concerns. This is a valid sequential dependency within Revision Concerns.
- T056 (VIF Stability) is listed as running 'after T055'. T055 is in Revision Concerns. T056 is in Revision Concerns. This is a valid sequential dependency within Revision Concerns.
- T057 (Report Reproducibility) is listed as running 'after T056'. T056 is in Revision Concerns. T057 is in Revision Concerns. This is a valid sequential dependency within Revision Concerns.
