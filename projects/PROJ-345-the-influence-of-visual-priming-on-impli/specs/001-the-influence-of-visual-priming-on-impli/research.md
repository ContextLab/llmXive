# Research: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Research Question & Hypotheses
| Hypothesis | Direction |
|------------|-----------|
| **H1** (Main effect) | Negative‑valence primes → longer IAT response times (RT) |
| **H2** (Interaction) | The valence‑RT link is stronger for high‑ambiguity targets |
| **H3** (Framing) | All effects are reported as **associational** (FR‑003) |

## 2. Dataset Strategy
| Dataset | Purpose | Verified URL | Load Method | Notes |
|---|---|---|---|---|
| **OpenIAT** (primary) | IAT response‑time data with trial‑level `response_time`, `participant_id`, `stimulus_id`, and stimulus metadata | `https://huggingface.co/datasets/openai/open_iat/resolve/main/iat.parquet` | `datasets.load_dataset(..., streaming=False)` | Contains all required columns; images are stored under the `stimuli/` folder referenced in the dataset metadata. |

*If the OpenIAT dataset is unavailable or the URL changes, the pipeline will abort with a clear “Data Gap” message before any analysis, satisfying FR‑001 and SC‑001.*

## 3. Statistical Methodology
### 3.1 Model Specification (conditional on available covariates)

**Full model (if demographics are present):**  
`RT_ij = β0 + β1·Valence_i + β2·Ambiguity_i + β3·(Valence×Ambiguity)_i + β_age·Age + β_gender·Gender + β_edu·Education + u0j + u1j·Valence_i + ε_ij`

- `u0j` = random intercept for participant *j*  
- `u1j` = random **slope** for prime valence per participant (addresses concern methodology‑49a4a36c)  
- Robust (Huber‑White) SE because predictors are derived (FR‑001/FR‑002).

**Reduced model (if ambiguity is unavailable):**  
Only the main effect of `Valence` is retained; the scope is recorded in `state/analysis_scope.json` as `"valence_only"`.

### 3.2 Rigor & Corrections
- **Multiple comparisons** – Benjamini‑Hochberg FDR on all fixed‑effect p‑values (FR‑004).  
- **Collinearity** – VIF computed **before** fitting (Task T010). VIF > 5.0 flags `claim_suppressed: true` and prevents independent effect claims (FR‑005).  
- **Power** – A priori power analysis (f = 0.15, α = 0.05, power = 0.80 → N ≈ 350). **Task T021** checks the post‑filter trial count against this target; if insufficient, the PDF includes a “Power Limitation” note (SC‑002).  
- **Causal framing** – All statements are explicitly associational (FR‑003).  
- **Measurement validity** – Valence and ambiguity scores are derived proxies; **Task T020** validates them against external benchmarks (NRC VAD lexicon for words, FER‑2013 for images) and reports validation metrics. If validation correlations fall below 0.6, a caution note is added to the report (addresses methodology‑c1f3b31e and scientific_soundness‑0f39757b).  

### 3.3 Derivation Strategy (mutually independent)
- **Valence** – lexical valence dictionary for word stimuli; CPU‑only emotion classifier (`torch` on CPU) for image stimuli (FR‑002).  
- **Ambiguity** – WordNet sense‑count for words; Laplacian texture variance for images.  

### 3.4 Sensitivity Analysis (FR‑006)
α ∈ {0.01, 0.05, 0.10}; re‑evaluate FDR‑corrected significance at each level; results stored in `reports/sensitivity_analysis.csv` and summarized in the PDF.

## 4. Compute Feasibility
- All steps run on 2 CPU cores, ≤7 GB RAM, ≤6 h.  
- No GPU is required; the CPU‑only emotion classifier fits comfortably within the memory budget.  
- Streaming support (Task T017) guarantees that even a >7 GB dataset can be processed without exceeding RAM.

## 5. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| **Hard‑coded URL in `config.py`** | Guarantees deterministic ingestion; URL is validated against the authoritative `verified_sources.json`. |
| **Threshold in `config.py`** | Eliminates circular task dependencies; all tasks read the same static value. |
| **VIF pre‑fit** | Prevents fitting a collinear model; aligns with FR‑005. |
| **Derived Scores Validation** | Provides external construct‑validity evidence for the derived predictors (addresses methodology‑c1f3b31e & scientific_soundness‑0f39757b). |
| **Power‑check checkpoint** | Ensures the analysis meets a priori power requirements before proceeding (addresses methodology‑e9a77e04). |
| **Confounding diagnostics** | Detects trial‑order and stimulus‑specific confounds that could bias results (addresses methodology‑e281f6e1). |
| **Random slope for prime valence** | Allows participant‑level variation in prime effects, yielding a more accurate mixed‑effects model (addresses methodology‑49a4a36c). |
| **Always‑generated PDF** | Satisfies SC‑003 even when the pipeline halts early. |
| **Streaming verification with >7 GB synthetic file** | Meets the requirement that streaming logic be exercised on a truly large file (Task T017). |
| **`verified_sources.json` as single source of truth** | Resolves ambiguity in T048; the file’s schema is enforced by `contracts/verified_sources.schema.yaml`. |
| **`pip.conf` with CPU‑only index URL** | Ensures deterministic installation of the CPU‑only Torch wheel (addresses T003a). |
| **Artifact hashing for all outputs** | Guarantees full compliance with Principle V (addresses plan_consistency‑37a6cd95). |

---

