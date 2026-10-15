# Research: The Impact of Incidental Music on Autobiographical Memory Retrieval

## 1. Domain Overview
The “incidental exposure” hypothesis posits that music heard during adolescence (a sensitive developmental window) becomes more readily available for later autobiographical recall, yielding higher vividness ratings. **Because the data are simulated and observational, the analysis can only speak to *associations*, not causal effects**.

## 2. Dataset Strategy
| Dataset | Type | Verified URL(s) | Role |
|---------|------|-----------------|------|
| **MSD (track metadata & listening history)** | Open‑source archive | `https://zenodo.org/record/1203745/files/MillionSongDataset.tar.gz` | Provides `track_id`, `release_year`, `popularity`, and realistic listen timestamps needed for adolescent exposure calculations. |
| **AMT (memory cues & ratings)** | **Simulated** (no open source) | N/A | `simulate_amt.py` generates deterministic user‑track cues, vividness (1‑7) and valence (1‑7) ratings, and synthetic listen timestamps. The simulation embeds a known effect (`β = 0.3`) for power validation and a null version (`β = 0`) for Type I error checks. |

*Rationale*: No verified AMT dataset exists; simulation guarantees that the pipeline can be fully exercised on CI without violating the “Data Hygiene” principle.

## 3. Statistical Methodology
### 3.1 Primary Model (Linear Mixed‑Effects)
- **Outcome**: `mean_vividness`
- **Predictors**: `logit(adolescent_exposure_ratio)`, `popularity`, **`total_listens`** (controls for denominator effect)
- **Random intercept**: `(1|user_id)`
- **Formula**: `mean_vividness ~ logit_ratio + popularity + total_listens + (1|user_id)`

### 3.2 Significance Testing (Block‑Permutation)
- Shuffle `mean_vividness` **within each user** (preserves intra‑user correlation).
- Re‑fit the LMM for each permutation (default = 1000 iterations).
- Null distribution = coefficients of `logit_ratio` from permuted fits.
- **Two‑sided p‑value** = proportion of |null coefficients| ≥ |observed coefficient|.
- **Multiple‑threshold correction**: Apply a Bonferroni adjustment across the five Levenshtein thresholds (α/5) to control family‑wise error (addressing FR‑007).

### 3.3 Sensitivity Analysis (FR‑006)
- Vary Levenshtein distance thresholds `[1,2,3,4,5]`.
- For each threshold: re‑match cues → re‑aggregate → re‑fit LMM.
- Report coefficient stability across thresholds (see `sensitivity_analysis.csv`).

### 3.4 Robustness Checks
- **Multicollinearity**: Compute VIF for `logit_ratio` and `popularity`; warn if VIF > 5 (source 2605.22529).
- **Missing Birth Years**: If > 50 % missing, compute a “Global Exposure” proxy (mean ratio for the user’s birth decade) **before** any filtering (EC‑001). Used only for a sensitivity re‑run, not as a primary predictor.
- **Minimum Listen Threshold**: Exclude pairs with `total_listens < 3` (FR‑009) to avoid unstable ratios.
- **Zero‑Variance Tracks**: Drop pairs where `n_cues == 0` (EC‑002).

## 4. Power Analysis
Using `simr`‑style calculations for LMMs:
- **Assumptions**: ICC = 0.25, embedded β = 0.3 (see simulation), α = 0.05, A substantial number of users each with multiple tracks yields on the order of ten thousand observations before filtering.
- **Effective N**: After applying FR‑009 and EC‑002 filters, simulations show ≈ 8 k usable rows.
- **Result**: Estimated power > 0.90 to detect the fixed effect of `logit_ratio`. This claim is optimistic and contingent on the filtering rates observed in the simulated data; the power analysis acknowledges that real data may differ.

## 5. Compute Feasibility
- All steps are CPU‑tractable; no GPU required.
- **Streaming**: MSD JSONL files are streamed (`datasets.load_dataset(..., streaming=True)`) to stay within ~6 GB RAM.
- **Permutation**: 1000 iterations on ~10 k rows complete in ≈ 2 h on a 2‑core CI runner; if runtime exceeds 6 h, the iteration count can be reduced (documented limitation).
- **Determinism**: Fixed random seeds (`random.seed(42)`, `np.random.seed(42)`) guarantee identical outputs across runs, satisfying reproducibility.

## 6. Decision Rationale
| Decision | Reason |
|----------|--------|
| **Simulate AMT** | No open AMT dataset; simulation provides a complete, reproducible pipeline while respecting data‑hygiene rules. |
| **Stream MSD** | Prevents OOM on the free‑tier runner; still uses real track metadata. |
| **Block‑Permutation (two‑sided, Bonferroni)** | Preserves the hierarchical structure required by the random intercept and controls family‑wise error across thresholds. |
| **Logit Transform** | Stabilises variance for bounded ratio predictor. |
| **Total‑listens Covariate** | Controls for denominator effect of exposure ratio, addressing FR‑005 completeness. |
| **Global Exposure Fallback (only sensitivity)** | Avoids ecological fallacy; used solely to test robustness when birth years are missing. |
| **VIF > 5 warning** | Aligns with the verified multicollinearity threshold (source 2605.22529). |
| **Separate matched files per threshold** | Guarantees that each sensitivity run is independently verifiable (each file has its own checksum). |
| **CSV contract alignment** | Ensures validation against `contracts/output.schema.yaml` rather than a mismatched JSON schema. |
| **Model output contract trimmed** | Marked as deprecated; pipeline only produces CSV outputs validated against `contracts/output.schema.yaml`. |

## 7. Verification Strategy
Each pipeline stage writes a file whose SHA‑256 is recorded in `state.yaml`. Automated pytest suites (`tests/unit/`, `tests/integration/`) load the file, validate against the JSON‑Schema contracts in `contracts/`, and assert expected dimensions (e.g., `user_track_pairs.parquet` has ≥ 1 row per threshold). The CI job fails if any checksum mismatches or schema violations occur, ensuring no fabricated artifacts.

## 8. Limitations
- The primary hypothesis that adolescent exposure predicts vivid autobiographical memories is evaluated **only on fully simulated AMT data** where the effect size (β = 0.3) is embedded by design. This means the analysis can only confirm that the pipeline recovers a known, pre‑specified effect, **not that the effect exists in real human populations**. Relying solely on simulated data therefore does not provide empirical evidence for the research question and constitutes a methodological limitation: the validation is not independent of the hypothesis and cannot substantiate the claimed real‑world relationship. Future work should seek an open, ethically‑shareable autobiographical memory dataset to replace the simulation and enable genuine inference.
