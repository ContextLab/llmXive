# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `task-format` (rejected 1x): Tasker must repair ambiguous task identities while preserving requirements. Malformed: ['- [ ] T019/T020 [US1] [FR-003] ICA blink‑component detection (frontal correlation >\u202f0.8) and removal, with removed‑component count logged → `data/processed/epo_clean.fif`. Verified.', '- [ ] T022a/T022b [US2] [FR-004] Per‑participant standard/deviant ERPs and difference waves → `data/processed/diff_wave.fif`. Verified.', '- [ ] T023/T024/T025 [US2] [FR-004] [SC-005] Peak detection (primary 150–250\u202fms, fallback 100–300\u202fms, ≥2.0\u202fµV threshold), `peak_detected` flagging, and SNR computation on difference waves at Fz/FCz. Verified.', "- [ ] T029–T035, T039, T039b [US3] [FR-005] [FR-006] Statistical analysis in `code/stats.py`: exclusion filtering, paired t‑tests (Wilcoxon fallback), FDR over 4 comparisons, mixed‑effects model, cluster‑based permutation test (1000 permutations), Cohen's\u202fd + 95\u202f% CI, prevalence, latency‑window validation → `results/statistics.json`, `results/latency_validation.json`. Verified.", '- [ ] T050/T051/T052 Integration/unit tests for preprocessing, extraction, FDR, and visualization. Verified.']; duplicates: []

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

