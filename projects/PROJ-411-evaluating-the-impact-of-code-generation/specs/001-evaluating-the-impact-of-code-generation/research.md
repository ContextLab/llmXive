# Research: Evaluating the Impact of Code Generation on Code Review Burden

## Dataset Strategy

| Dataset | Verified Source URL | Role | Loader | Key Variables Needed |
|---------|---------------------|------|--------|----------------------|
| **Primary PR population** | https://huggingface.co/datasets/loubnabnl/prs-v2-sample/resolve/main/data/train-00000-of-00001-a3494cf8c0712e34.parquet | Main analysis (both LLM‑generated and Human‑written PRs) | `datasets.load_dataset('loubnabnl/prs-v2-sample', split='train')` (as pandas) | `pr_id`, `repo_name`, `created_at`, `merged_at`, `additions`, `deletions`, `comment_count`, `commit_message`, `diff_text`, `file_headers`, `labels`, `first_comment_timestamp` |
| **Auxiliary known‑LLM set A** | https://huggingface.co/datasets/prs-eth/AGBD/resolve/main/embeddings_train.csv | Validation of provenance signals (known LLM PRs) | `datasets.load_dataset('prs-eth/AGBD', split='train')` (CSV) | `commit_message` (contains LLM keywords), minimal review fields |
| **Auxiliary known‑LLM set B** | https://huggingface.co/datasets/prs-eth/AGBD-Lite/resolve/main/AGBD-Lite-test.h5 | Same as above (alternative source) | `datasets.load_dataset('prs-eth/AGBD-Lite', split='train')` (H5) | `commit_message`, minimal metadata |

All files are downloaded programmatically; SHA‑256 checksums are recorded in `data/checksums.txt`. No other data sources are used.

### Why the primary comparison stays within the **single** primary dataset
The auxiliary datasets consist of PRs that are *purpose‑built* for LLM‑generated code (e.g., model‑card edits). Mixing them with the general PR population would confound provenance with repository type and PR purpose. By restricting the binary LLM vs Human comparison to the **single** verified PR corpus (`prs-v2-sample`) and assigning group membership via FR‑002 signals, we eliminate dataset‑origin bias. We still report a **group × source contingency table** and a **source‑stratified descriptive analysis** of the auxiliary sets for transparency (see Phase 1 & Phase 6).

### Per‑dataset variable availability (Phase 0 verification)

| Variable | Primary parquet | AGBD CSV | AGBD‑Lite H5 | Comment |
|----------|----------------|----------|--------------|---------|
| `pr_id` | ✅ | ✅ | ✅ | Required for all phases |
| `repo_name` | ✅ | ✅ | ✅ | Required |
| `created_at` / `merged_at` | ✅ | ✅ | ✅ | Needed for duration metrics |
| `additions`, `deletions` | ✅ | ✅ | ✅ | Combined → `lines_changed` |
| `comment_count` | ✅ | ✅ | ✅ | Required for FR‑003 filter |
| `commit_message` | ✅ | ✅ | ✅ | LLM keyword detection |
| `diff_text` | ✅ (may be null) | ❌ | ❌ | Used only when present |
| `file_headers` | ✅ (may be null) | ❌ | ❌ | Highest‑precedence provenance signal |
| `labels` | ✅ | ✅ | ✅ | Issue‑severity extraction |
| `first_comment_timestamp` | ✅ (may be null) | ❌ | ❌ | Required for `review_active_seconds`; fallback noted |

If any required variable is missing from the **primary** dataset, Phase 0 aborts and reports the mismatch for scope revision. Missing variables in the auxiliary sets are acceptable because they are used only for provenance validation (FR‑007) where the missing fields do not affect the required analysis.

## Decision / Rationale

| Decision | Rationale | CPU / GPU |
|----------|-----------|-----------|
| Use **verified** HuggingFace parquet/CSV/H5 files instead of live GitHub API | Guarantees unattended CI execution, respects rate‑limit constraints, and satisfies FR‑001/FR‑009 via a no‑op backoff. | CPU |
| Primary binary comparison limited to `loubnabnl/prs-v2-sample` | Avoids dataset‑origin confounding; provenance is derived per‑PR, not per‑source. | CPU |
| Classification hierarchy (header > diff > keyword) enforced in `classify_provenance.py` | Direct implementation of FR‑002 and Constitution VI; unit test `test_precedence_header_wins` verifies correct behavior. | CPU |
| Mixed‑effects model with `repo_name` random intercept + fixed covariates (`lines_changed`, `author_experience`, `repository_popularity`, `creation_quarter`) | Satisfies FR‑013 (within‑repo non‑independence) and controls known confounders; uses `statsmodels.MixedLM` (CPU‑tractable). | CPU |
| Pre‑specify Mann‑Whitney U as primary test; report Welch t‑test alongside | Normality tests are expected to reject at scale; the companion test provides robustness without changing conclusions. | CPU |
| Bonferroni correction across all primary metrics | Controls family‑wise error as required by the multiplicity assumption in the spec. | CPU |
| Power analysis based on medium effect (d = 0.5) → n ≈ 64/group (t‑test) and ≈ 70/group for rank‑based test | Required by FR‑019; limitation statements added if thresholds are not met. | CPU |
| Sensitivity sweeps over IQR {1.0, 1.5, 2.0} and comment‑filter ≥ 0 | Implements FR‑006, FR‑014, and SC‑003. | CPU |
| Manual κ validation on a **fixed** 50‑PR‑per‑group sample (`validation_sample.csv`) | Guarantees reproducibility; κ ≥ 0.6 required (SC‑001). | CPU |
| Observational framing only | No random assignment; causal claims are prohibited by the assumptions section. | CPU |
| Resource monitoring via `psutil` | Enforces SC‑005 (CPU/RAM limits). | CPU |

All decisions are CPU‑first; no GPU escape hatch is needed.

## Statistical Validation Discipline

1. **Normality** – Shapiro‑Wilk (α = 0.05) per metric per group; results logged. Mann‑Whitney U is the *designated* primary test; Welch t‑test is always reported as a companion.  
2. **Primary tests** – `review_active_seconds` and `comment_density` via Mann‑Whitney U (rank‑biserial) plus Welch t‑test (Cohen’s d). `issue_severity` via chi‑square (Cramér’s V).  
3. **Effect sizes** – Reported regardless of significance; validated on a synthetic benchmark (±0.05 tolerance, FR‑005).  
4. **Multiplicity** – Bonferroni‑adjusted α = 0.05 / k (k = number of primary metrics actually tested).  
5. **Null‑result statement** – Automatically inserted when p ≥ α (FR‑011).  
6. **Robustness flag** – Set if any significance flips across IQR thresholds or comment‑filter relaxation (SC‑003).  
7. **Collinearity** – VIF computed for `lines_changed` vs. `comment_density`; if VIF > 5, report joint relationship only.  
8. **Power** – Verify n ≥ 64/group (t‑test) and ≈ 70/group (rank‑based); otherwise add a limitation paragraph (FR‑019, SC‑007).  
9 **Temporal confounding** – Include `creation_quarter` as a fixed effect; run a stratified sensitivity check.  

All statistical procedures are implemented with `scipy`, `statsmodels`, and `scikit-learn`.

## Validation & Sensitivity

- **Inter‑rater agreement** – `sklearn.metrics.cohen_kappa_score` on `manual_labels.csv`; κ ≥ 0.6 required (SC‑001).  
- **Misclassification response** – Estimate false‑negative rate in the Human‑written group; if > 10 % report attenuation, re‑run analysis excluding keyword‑negative PRs from high‑LLM prevalence repos, and note the limitation.  
- **Outlier thresholds** – IQR = 1.0, 1.5, 2.0; record significance flips in `sensitivity_report.csv`.  
- **Comment‑filter sensitivity** – Re‑run with `comment_count ≥ 0`; report any flip.  
- **Selection bias (FR‑018)** – Compare Mixed PRs vs. pure groups on size, comment density, severity; report any significant differences.  
- **Dataset‑origin sensitivity** – Descriptive statistics for the two auxiliary known‑LLM sets (where outcome fields exist); never pool with the primary comparison.  

All outputs conform to the schemas defined in `contracts/`.

## Resource Monitoring

Each script invokes a small `psutil` wrapper that logs `peak_memory_mb` and `cpu_seconds`. If `peak_memory_mb` > 6500 MB or cumulative `cpu_seconds` > 21600 s (6 h), the pipeline aborts with a clear error message, satisfying SC‑005.

---
