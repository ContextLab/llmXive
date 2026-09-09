# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 55 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T033b (Correlation) depends on T033 (Re-fit CLMM) AND T029 (Primary Results). T033 depends on T032. T032 depends on T019. The flow is T019 -> T032 -> T033 -> T033b. Also T029 -> T033b. This is correct. T033b needs the primary model (from T027a, saved in T029? No, T027a saves the model. T029 saves results. T033b loads 'clmm_model.pkl' from T027a. The dependency on T029 is for the primary results? T033b says 'Dependency: T033, T029'. T029 produces 'clmm_results.csv'. T033b needs the model object (from T027a) and the robustness model (from T033). The dependency on T029 might be unnecessary if T033b only needs the model files, but T029 ensures the primary results are finalized. This is acceptable.
- T007b (Record checksums) depends on T007 (Data integrity). T007 is marked [P] in Phase 1. T007b is NOT marked [P] and has a logic note 'Dependency: T007. Must wait for T007 to complete.' This is correct. The [P] tag on T007 is fine as it has no dependencies. T007b correctly waits for T007.
- The US1 implementation tasks are ordered T015 (Download) -> T016 (Validate) -> T017 (Filter) -> T018 (Transform) -> T019 (Merge/Score). This is a correct producer-consumer chain. T015 produces raw data, T016 consumes it to validate, T017 consumes validated data to filter, T018 consumes filtered data to transform, T019 consumes transformed data to merge and score. The ordering is correct.
- T025 (Load data) -> T026 (VIF check) -> T027a (CLMM Fitting). T026 depends on T025? The logic for T026 says 'Dependency: T026' (typo, should be T025). T027a depends on T026. The flow is correct: Load -> Check Collinearity -> Fit Model. The dependency on T025 for T026 is implied but not explicitly stated in T026's logic (it says 'Dependency: T026' which is a typo). This is a minor documentation error but the intended order is correct.
- T042 (Configure CI) -> T042b (Execute CI) -> T043 (Generate Report). T042b depends on T042. T043 depends on T042b. This is correct. T042b produces metrics, T043 consumes them. The ordering is correct.
- T012 (Sample Size Verification) depends on T019 (Merge). T019 is in Phase 3. T012 is in Phase 4. The ordering is correct. T012 must run after data is merged and scored.
- T032 (Robustness Scoring) depends on T019 (US1 completion). T019 is in Phase 3. T032 is in Phase 6. The ordering is correct. T032 needs the merged and scored data from T019.
- T035 (Multiplicity Correction) depends on T034. T034 is in Phase 6. T035 is in Phase 6. The ordering is correct. T035 needs the subgroup results from T034.
- T037 (Save robustness results) depends on T032, T033, T033b, T034, T035. All these are in Phase 6. T037 is the final step in Phase 6. The ordering is correct.
- T004 (CI workflow) and T004b (R environment) are both in Phase 1 and marked [P]. T004b installs R packages. T004 sets up the CI workflow. They are independent. The [P] tags are correct.
- T006 (PII scanner) and T007 (Data integrity) are both in Phase 1 and marked [P]. They are independent. The [P] tags are correct.
- T013 and T014 are tests for US1. They are marked [P] and are in Phase 3. The logic says 'Write these tests FIRST, ensure they FAIL before implementation'. This implies they should be done before T015-T019. However, they are listed after the 'Implementation for User Story 1' section. The ordering in the document is Tests -> Implementation. This is correct for TDD. The [P] tags are correct as they are independent tests.
- T023 and T024 are tests for US2. They are marked [P] and are in Phase 5. The logic says 'Write these tests FIRST'. They are listed before the implementation tasks T025-T029. This is correct for TDD. The [P] tags are correct.
- T030 and T031 are tests for US3. They are marked [P] and are in Phase 6. The logic says 'Write these tests FIRST'. They are listed before the implementation tasks T032-T037. This is correct for TDD. The [P] tags are correct.
- T039 (Code cleanup), T040 (Performance), T041 (Additional tests) are in Phase 7. They are marked [P]. They are independent. The [P] tags are correct.
- T042, T042b, T043 are in Phase 7. T042b depends on T042. T043 depends on T042b. The ordering is correct. T042 is marked [P] (no dependencies). T042b and T043 are not marked [P] due to dependencies. This is correct.
- T007b is in Phase 1. It depends on T007. T007 is marked [P]. T007b is not marked [P]. This is correct.
- T008 is in Phase 1. It is marked [P]. It has no dependencies. This is correct.
- T010 is in Phase 1. It is marked [P]. It has no dependencies. This is correct.
- T010b is in Phase 1. It is marked [P]. It has no dependencies. This is correct.
- T012 is in Phase 4. It depends on T019. It is marked [P]. This is incorrect. T012 has a dependency on T019, so it cannot be parallel-safe with T019. The [P] tag on T012 is a violation. T012 must wait for T019 to complete. It should not be marked [P].
- T015 is in Phase 3. It is marked [P]. It has no dependencies (after Phase 2). This is correct.
- T016 is in Phase 3. It depends on T015. It is not marked [P]. This is correct.
- T017 is in Phase 3. It depends on T016. It is not marked [P]. This is correct.
- T018 is in Phase 3. It depends on T017. It is not marked [P]. This is correct.
- T019 is in Phase 3. It depends on T018. It is not marked [P]. This is correct.
- T025 is in Phase 5. It is marked [P]. It has no dependencies (after Phase 2). This is correct.
- T026 is in Phase 5. It depends on T025. It is not marked [P]. This is correct.
- T027a is in Phase 5. It depends on T026. It is not marked [P]. This is correct.
- T028 is in Phase 5. It depends on T027a. It is not marked [P]. This is correct.
- T029 is in Phase 5. It depends on T028. It is not marked [P]. This is correct.
- T032 is in Phase 6. It depends on T019. It is not marked [P]. This is correct.
- T033 is in Phase 6. It depends on T032. It is not marked [P]. This is correct.
- T033b is in Phase 6. It depends on T033 and T029. It is not marked [P]. This is correct.
- T034 is in Phase 6. It depends on T012 and T019. It is not marked [P]. This is correct.
- T035 is in Phase 6. It depends on T034. It is not marked [P]. This is correct.
- T037 is in Phase 6. It depends on T032, T033, T033b, T034, T035. It is not marked [P]. This is correct.
- T038a, T038b, T038c are in Phase 7. They are marked [P]. They are independent. This is correct.
- T042 is in Phase 7. It is marked [P]. It has no dependencies. This is correct.
- T042b is in Phase 7. It depends on T042. It is not marked [P]. This is correct.
- T043 is in Phase 7. It depends on T042b. It is not marked [P]. This is correct.
- Task T002 instructs to create `code/requirements.txt` containing 'ordinal', but the task logic explicitly states 'ordinal is an R package and must NOT be in this list'. The task description contradicts its own logic, making it impossible to execute deterministically without guessing the intent.
- Task T015 lists three datasets (HCI_P2, Persona-Chat, EmpatheticDialogues) but the spec (FR-001) only mandates two. The task does not define the canonical HuggingFace repository paths for 'HCI_P2' or 'Persona-Chat' (e.g., 'HuggingFaceH4/hci_p2' vs 'huggingface/hci_p2'). Without exact repo IDs, the implementer cannot deterministically fetch the data.
- Task T019 requires computing 'conversation_length' but does not specify the unit (word count vs. utterance count). The spec (Assumptions) allows either, but the task must be deterministic. The implementer cannot know which metric to use without external context.
- Task T028 introduces a dynamic switching logic (Bonferroni if N ≤ 3, else BH) not present in the spec. While this resolves a spec ambiguity, the task does not define 'N' (number of hypothesis tests) explicitly (e.g., 'count of fixed effects in the model'). The implementer cannot calculate N deterministically without knowing the exact model formula implementation details.
- Task T032 requires attempting to load 'LIWC-2015' from a specific path or HF, but does not provide the HF repo ID or the exact filename for the dictionary. If the local path fails, the implementer cannot deterministically attempt the HF download without the specific repo identifier.
- Task T033b requires calculating Spearman correlation between 'primary_predicted_quality' and 'robust_predicted_quality'. However, the task does not specify how to generate these 'predicted quality' scores (e.g., using the model's `predict()` method on the original data, or a specific transformation). The exact input data and method for prediction are missing.
- Tasks T001a through T001d are too coarse. They group multiple directory creation actions into single tasks. The atomizer will split these, but for executability, each directory creation should be a distinct, verifiable step (e.g., 'Create data/raw', 'Create data/processed').
- Tasks T015, T016, and T017 are overly granular and tightly coupled (Download -> Validate -> Filter). While the atomizer handles splitting, these tasks are not self-contained; T016 depends on T015's output format which is not fully defined in T015's description. They should be merged into a single 'Download and Validate' task or T015 must explicitly define the output schema for T016.
- Task T032 implements a mandatory fallback to 'textstat' if LIWC-2015 acquisition fails. This violates FR-005 which mandates the system MUST re-run analysis with the 'LIWC-2015 Politeness Dictionary'. Allowing a different classifier (textstat) to satisfy the requirement silently weakens the functional constraint to an 'attempt' rather than a 'must', violating the spec's strict requirement for a specific alternative classifier.
- Tasks T015-T019 mandate downloading and merging a third dataset (HCI_P2) not listed in FR-001 (which specifies only Persona-Chat and EmpatheticDialogues). While the plan.md mentions three datasets, the tasks implement this scope expansion without a corresponding update to the spec's FR-001 or a documented justification for the additional data source in the task logic, creating a silent drift from the defined functional requirements.
- Task T028 introduces a dynamic switching logic (Bonferroni if N ≤ 3, else Benjamini-Hochberg) to satisfy FR-004. The spec does not authorize this runtime-dependent decision rule. This creates a testability gap where the 'correct' correction method depends on data counts rather than a deterministic spec-defined algorithm, violating the requirement for a fixed, verifiable multiple-comparison correction strategy.
- Task T027a implements a silent fallback to a fixed-effects model upon CLMM convergence failure. SC-003 requires measuring a ≥95% convergence rate for the CLMM. The task does not specify whether the fallback model counts toward this metric or if the convergence failure is logged as a failure against the SC-003 threshold. This ambiguity allows the system to pass the pipeline while potentially failing the success criterion, weakening the constraint.
- Task T016 focuses on excluding entire *sources* if the 'quality_rating' column is missing. The spec's Edge Cases explicitly require handling the exclusion of *individual dialogues* lacking ratings within a valid source. The task logic omits this granular filtering step, creating a gap where invalid dialogues might be retained, violating the data hygiene and filtering constraints defined in the spec.
- Task T019 does not specify whether 'conversation_length' is computed as word count or utterance count. The spec's Assumptions state 'Conversation length can be computed as word count or utterance count', but the task fails to lock this definition. This lack of definition makes the resulting model coefficients non-reproducible and violates the requirement for a deterministic implementation of the CLMM formula.
