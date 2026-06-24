# Tasks

- [ ] T001 [REV] Address action item **[6e267887ca5a]** (severity: writing): Provide the correct SHA‑256 hash of specs/001-knot-complexity-analysis/tasks.md and replace the placeholder in the review front‑matter.
- [ ] T002 [REV] Address action item **[137a57c5c9fc]** (severity: writing): Populate docs/reproducibility/data_quality_report.md with the actual counts of data_quality_flags and missing_invariant_flags (e.g., “data_quality_flags: 0”, “missing_invariant_flags: 12”).
- [ ] T003 [REV] Address action item **[57718f0a2f6f]** (severity: writing): Replace the VIF placeholders in docs/reproducibility/multicollinearity_assessment.md with the computed VIF values for crossing number and braid index.
- [ ] T004 [REV] Address action item **[16b8994dfbab]** (severity: writing): Fix the tie‑breaking validation so that docs/reproducibility/tie_breaking_validation.md reports success, or adjust the validation script and re‑run it to produce a passing result.
- [ ] T005 [REV] Address action item **[270b9fca2f74]** (severity: writing): Correct the dataset size report in docs/reproducibility/dataset_counts.md (and any derived counts) to reflect the true number of prime knots (≈ 9 988 for ≤ 13 crossings) and ensure consistency with data/processed/knots_cleaned.csv.
- [ ] T006 [REV] Address action item **[631d68986bcb]** (severity: writing): Consolidate checksum manifests to a single authoritative file (e.g., keep only data/checksums.sha256 and remove/ignore the CSV and JSON versions), updating any scripts that reference them.
- [ ] T007 [REV] Address action item **[99a6d9eaf71b]** (severity: writing): Verify duplicate‑record handling by confirming that the cleaned dataset contains zero duplicate knot_ids and record this fact in the data‑quality report.
