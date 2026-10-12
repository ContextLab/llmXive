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
| **ia_test_embeddings** (primary) | Candidate IAT‑style data | `https://huggingface.co/datasets/davanstrien/ia_test_embeddings/resolve/main/data/train-00000-of-00001-82feb90c086b8e08.parquet` | `datasets.load_dataset(..., streaming=False)` | **Dataset‑variable audit:** does **NOT** contain `response_time`, `participant_id`, or `stimulus_id`. The ingestion gate (Task T003) will halt with `Data Gap: Schema Mismatch`. |
| Other verified URLs (iati, OSF, GET, OAuth) | Explored as alternatives | See “Verified datasets” block | Appropriate loader per format | **None** contain the required trial‑level IAT columns. |

### Data Availability Assessment (Fatal‑Flaw Audit)
- The spec requires trial‑level response times, stimulus IDs, and prime/target image linkage.  
- **No** verified dataset in the provided block supplies these variables.  
- Consequently the pipeline **cannot** produce substantive statistical results until a suitable open IAT dataset is added to `data/verified_sources.json` and referenced in `code/config.py`.  
- The plan therefore includes an **honest data‑gap halt** (Task T003) and produces a PDF reporting this limitation. No synthetic data or fabricated mirrors are used, satisfying the fabrication gate.

## 3. Statistical Methodology
### 3.1 Model Specification (conditional on available covariates)

**Full model (when demographics present):**  
`RT_ij = β0 + β1·Valence_i + β2·Ambiguity_i + β3·(Valence×Ambiguity)_i + β_age·Age + β_gender·Gender + β_edu·Education + u_j + ε_ij`

- `u_j` = random intercept for participant *j* (repeated measures).  
- Robust (Huber‑White) SE because predictors are derived (FR‑001/FR‑002).  

**Reduced model (if ambiguity unavailable):**  
Only the main effect of `Valence` is retained; `analysis_scope.json` records `"valence_only"`.

### 3.2 Rigor & Corrections
- **Multiple comparisons** – Benjamini‑Hochberg FDR on all fixed‑effect p‑values (FR‑004).  
- **Collinearity** – VIF computed on the design matrix *before* fitting (FR‑005). VIF > 5.0 sets `claim_suppressed: true` and the report avoids independent‑effect language.  
- **Correlation check** – Pearson |r| > 0.7 between `Valence` and `Ambiguity` leads to dropping the interaction term with a logged warning.  
- **Power** – Approximate a priori power analysis (small‑to‑medium effect f = 0.15, α = 0.05, power = 0.80 → N ≈ 350 trials). If the post‑filter dataset is smaller, a “Power Limitation” note is added to the PDF (SC‑002).  
- **Causal framing** – All statements are explicitly associational (FR‑003).  
- **Measurement validity** – Valence and ambiguity scores are model‑derived proxies; the report cites the dictionaries and the CPU emotion classifier but notes the lack of external validation (FR‑003).

### 3.3 Derivation Strategy (mutually independent)
- **Valence** – lexical valence dictionary for word stimuli; CPU‑only emotion classifier (`torch` on CPU) for image stimuli (FR‑002).  
- **Ambiguity** – WordNet sense‑count for words; Laplacian texture variance for images.  

### 3.4 Sensitivity Analysis (FR‑006)
α ∈ {0.01, 0.05, 0.10}; re‑evaluate FDR‑corrected significance at each level; results stored in `reports/sensitivity_analysis.csv` and summarized in the PDF.

## 4. Compute Feasibility
- All steps run on 2 CPU cores, ≤7 GB RAM, ≤6 h.  
- No GPU is required; the CPU‑only emotion classifier fits within the memory budget.  
- Streaming support (Task T014) guarantees that even a >7 GB dataset can be processed without exceeding RAM.

## 5. Decision Rationale
| Decision | Rationale |
|----------|-----------|
| **Hard‑coded URL in `config.py`** | Guarantees deterministic ingestion; URL is validated against the authoritative `verified_sources.json`. |
| **Threshold in `config.py`** | Eliminates circular task dependencies; the same value is used by both ingestion and linkage‑gate tasks. |
| **VIF pre‑fit** | Prevents fitting a collinear model; aligns with FR‑005. |
| **FDR over Bonferroni** | Retains power for exploratory interaction tests while controlling family‑wise error. |
| **Always‑generated PDF** | Satisfies SC‑003 even when the pipeline halts early. |
| **Streaming verification with >7 GB synthetic file** | Meets the requirement that streaming logic be exercised on a truly large file (Task T014). |
| **`verified_sources.json` as single source of truth** | Resolves ambiguity in T048; the file’s schema is enforced by `contracts/verified_sources.schema.yaml`. |
| **`pip.conf` with CPU‑only index URL** | Ensures deterministic installation of the CPU‑only Torch wheel (addresses T003a). |

---
