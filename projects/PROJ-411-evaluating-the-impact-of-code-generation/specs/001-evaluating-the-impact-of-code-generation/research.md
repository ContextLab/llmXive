# Research: Evaluating the Impact of Code Generation on Code Review Burden

## Dataset Strategy

| Dataset | Source URL (verified) | Role | Loader | Key Variables Needed |
|---------|-----------------------|------|--------|----------------------|
| PRs-v2-sample | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | **Primary population** — both LLM-labeled and Human-labeled PRs come from this single general GitHub PR sample, classified by FR-002 signals | `pandas.read_parquet(hf_hub_download(...))` | `pr_id`, `repo_name`, `created_at`, `merged_at`, additions/deletions, `comment_count`, commit-message text, diff/header text (if present), labels |
| Authors-merged-model-PRs | https://huggingface.co/datasets/davanstrien/authors_merged_model_prs/resolve/main/data/train-00000-of-00001-d32a63c5798549f1.parquet | **Auxiliary only** — known-LLM reference for classification-signal validation and source-stratified sensitivity; never pooled with the primary comparison | same | commit-message text; review-interaction fields expected absent |
| Authors-merged-dataset-PRs | https://huggingface.co/datasets/davanstrien/authors_merged_dataset_prs/resolve/main/data/train-00000-of-00001-d5c709e857d2ca0b.parquet | **Auxiliary only** — same as above | same | same |

SHA-256 checksums are recorded in `data/checksums.txt` on download. The three files are kept **separate** (tagged `source_dataset`); they are NOT concatenated into one analysis population. No other data sources are used; no dataset URLs are invented.

**Why the primary comparison stays within `prs-v2-sample`**: the two davanstrien datasets are curated collections of PRs authored by LLM agents on HuggingFace Hub repositories (largely model-card/dataset-metadata edits), while `prs-v2-sample` is a general GitHub PR sample. Pooling them would confound provenance with platform and PR-type (dataset-origin selection). Restricting the primary LLM-vs-Human comparison to a single population, with group membership determined by PR-level provenance signals, removes this confound by design. A group×source contingency table and a descriptive source-stratified sensitivity analysis are still reported.

**Per-dataset variable availability (verified at Phase 0, expected values stated up front)**: the davanstrien datasets are near-certainly missing review-interaction fields (`comment_count`, `first_comment_timestamp`, labels) and diff/header text — expected, and non-blocking because they are auxiliary. `prs-v2-sample` is expected to carry the PR-level fields; if a required outcome variable is missing there, the pipeline halts and reports the mismatch for scope revision. `first_comment_timestamp` may be absent even in `prs-v2-sample`, in which case `review_active_seconds` falls back to `review_duration_seconds` with an explicit limitation.

## Decision/Rationale

| Decision | Rationale | CPU/GPU |
|----------|-----------|---------|
| Use open HuggingFace parquet files instead of live GitHub API scraping | Reproducible, rate-limit-free, unattended-CI-friendly; the datasets are pre-extracted PR records. FR-001/FR-009 are satisfied by static downloads; the backoff guard is retained only for optional enrichment. | CPU |
| Primary comparison within `prs-v2-sample`; davanstrien sets auxiliary only | Removes dataset-origin/platform confounding (the davanstrien sampling frame is itself correlated with provenance); group membership is determined by PR-level signals, not source. | CPU |
| Classification precedence (file-header > diff pattern > commit keyword) | Mirrors FR-002 and Constitution Principle VI. | CPU |
| Mixed-effects model with `repo_name` random intercept + fixed effects (lines_changed, author_experience, repository_popularity where available, and PR creation quarter as a temporal covariate) | Addresses FR-013 (within-repository non-independence and known confounders) and temporal drift in review practices (LLM-assisted PRs concentrate in later windows). | CPU (statsmodels MixedLM) |
| Pre-specify Mann-Whitney U as the expected primary test; report Welch t-test as a robustness companion | Normality tests are consistent and reject trivially at scale, making "automatic selection" effectively deterministic; the companion test prevents conclusions from hinging on selection. | CPU |
| Bonferroni correction across primary tests | Controls family-wise error per the spec's multiplicity assumption. | CPU |
| A priori power analysis (d = 0.5, α = 0.05, power = 0.8 → n ≈ 64/group, t-test-based; ~70/group under the rank-based primary test) | Required by FR-019; limitation reported if either threshold is unmet. | CPU |
| Sensitivity analyses (IQR sweep {1.0, 1.5, 2.0}; comment-filter ≥ 0; source-stratified descriptive comparison) | Implements FR-006, FR-014, SC-003, and dataset-origin confound assessment. | CPU |
| Cohen's κ on a 50-PR-per-group manual sample via committed human labels, with a pre-planned misclassification response | Meets FR-007/SC-001 without fabricating labels; false-negative rate in the Human-written group drives attenuation limitations and a prevalence-based exclusion sensitivity analysis. | CPU |
| Observational framing: associational differences only | The study has no randomization or identification strategy; no causal claims. | CPU |
| Issue severity as a proxy metric with acknowledged construct-validity limits (no citation; the spec's "Jones et al., 2022" reference is unverified and kicked back for removal) | FR-012/FR-017; primary burden metrics remain `review_active_seconds` and `comment_density`. | CPU |
| **Compute choice**: all methods are CPU-tractable classical statistics (pandas/scipy/statsmodels/sklearn); no GPU escape hatch is needed. | Fits the 2-CPU / 7 GB / 6 h runner. | CPU |

## Statistical Validation Discipline

1. **Normality** – Shapiro-Wilk (α = 0.05) per metric per group, reported for transparency; Mann-Whitney U is pre-specified as the expected primary test (Shapiro-Wilk is consistent and rejects at scale), with the Welch t-test reported alongside every primary result as a robustness companion (FR-004).
2. **Primary tests** – `review_active_seconds` and `comment_density` (Mann-Whitney U with rank-biserial effect sizes, plus Welch t-test/Cohen's d companions); `issue_severity` distribution via chi-square with Cramér's V (SC-006).
3. **Effect sizes** – Cohen's d (t-test) or rank-biserial (Mann-Whitney U), reported regardless of significance; benchmarked against small/medium/large (0.2/0.5/0.8) per SC-004; validated on a synthetic benchmark with known effect within ±0.05 (FR-005).
4. **Multiplicity** – Bonferroni-adjusted α = 0.05 / k over primary tests.
5. **Null-result statement** – automatically inserted when p ≥ α (FR-011).
6. **Robustness flag** – set when significance flips across IQR thresholds or the comment-filter relaxation (SC-003).
7. **Collinearity** – VIF diagnostic for `lines_changed` vs. `comment_density`; if r > 0.8, joint reporting only.
8. **Power** – n ≥ 64/group (t-test basis) and ~70/group (rank-based basis) verified; otherwise limitation statement (FR-019, SC-007).
9. **Temporal confounding** – PR creation quarter included as a fixed effect in the mixed model; stratified-by-period sensitivity check; limitation stated regardless.

## Validation & Sensitivity

- **Inter-rater agreement** – `sklearn.metrics.cohen_kappa_score` on the committed manual-label file; κ ≥ 0.6 required (SC-001); groups with κ < 0.6 flagged for manual review and downgraded to descriptive reporting.
- **Misclassification response (pre-planned)** – estimate the false-negative rate in the Human-written group from the validation sample; if > 10%, report attenuation toward the null, run a sensitivity analysis excluding keyword-negative PRs from repositories with high LLM-PR prevalence, and record the limitation. Keyword-based classification has asymmetric error (signal-less LLM PRs are silently labeled Human), so this attenuation risk is stated up front.
- **Outlier thresholds** – IQR multipliers 1.0, 1.5, 2.0; results in `data/results/sensitivity_report.csv`.
- **Comment-filter sensitivity** – full re-run with `comment_count ≥ 0`; effect sizes and p-values compared (FR-014).
- **Selection bias (FR-018)** – Mixed-vs-pure group distribution comparisons reported.
- **Dataset-origin sensitivity** – group×source contingency table reported; descriptive source-stratified comparison of the known-LLM davanstrien PRs (where outcome fields exist) against primary-population groups, never pooled.

## Resource Monitoring

`psutil` records peak RAM and CPU time per script; the pipeline aborts with a clear log if limits are approached (SC-005). Expected footprint: the three parquet files are small enough to load in RAM; if any exceeds budget, rows are processed in chunks (never sampled down to a toy or synthetic substitute without an explicit, reported power limitation).