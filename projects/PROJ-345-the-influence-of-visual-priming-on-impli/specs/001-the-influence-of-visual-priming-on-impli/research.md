# Research: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

## 1. Research Question & Hypotheses
**Primary Question**: Does visual priming with emotionally valenced stimuli alter implicit attitudes (measured by IAT response times) toward ambiguous social stimuli, and is this effect moderated by stimulus ambiguity?

| Hypothesis | Direction |
|------------|-----------|
| **H1** (Main Effect) | Negative‑valence primes → longer RTs vs. positive‑valence primes |
| **H2** (Interaction) | The prime‑valence effect is amplified for high‑ambiguity targets |
| **H3** (Observational) | All reported relationships are **associational**, not causal (FR‑003) |

## 2. Dataset Strategy
| Dataset | Purpose | Verified URL | Load Method | Notes |
|---|---|---|---|---|
| **IAT Embeddings** | Primary IAT response times, stimulus IDs, optional demographics | `https://huggingface.co/datasets/davanstrien/ia_test_embeddings/resolve/main/data/train-00000-of-00001-82feb90c086b8e08.parquet` | `datasets.load_dataset("davanstrien/ia_test_embeddings", split="train", streaming=False)` | Contains `response_time`, `participant_id`, `stimulus_id`. Demographic columns (`age`, `gender`, `education`) may be absent; pipeline omits them if missing (see §3.1). |
| **OSF Loglikelihood (supplementary)** | Optional sanity‑check of stimulus‑order effects | `https://huggingface.co/datasets/cjziems/osf_loglikelihood/resolve/main/inconclusive/test-00000-of-00001.parquet` | `datasets.load_dataset("cjziems/osf_loglikelihood", split="test", streaming=False)` | Used only for the **confounding check** (trial order) and not for primary modeling. |

*No gated datasets (e.g., ADNI) are used. All URLs are directly downloadable without authentication, satisfying the compute‑feasibility requirement.*

### Data Availability Assessment
- The IAT dataset is ≤ 2 GB, comfortably fitting in RAM; however, the pipeline uses streaming mode for robustness against future larger releases.  
- Demographic columns are **optional**; the model will drop missing covariates and log a `Demographics Missing` flag.  
- Stimulus images referenced by `stimulus_id` are fetched from the public OSF repository (the same URL used for metadata extraction).  

## 3. Statistical Methodology

### 3.1 Model Specification (Conditional on Data Availability)
**Case A – Demographics present**  
\[
\text{RT}_{ij}= \beta_0 + \beta_1\text{Valence}_i + \beta_2\text{Ambiguity}_i + \beta_3(\text{Valence}_i \times \text{Ambiguity}_i) + \beta_{age}\text{Age}_i + \beta_{gender}\text{Gender}_i + \beta_{edu}\text{Education}_i + u_j + \epsilon_{ij}
\]

**Case B – Demographics missing**  
\[
\text{RT}_{ij}= \beta_0 + \beta_1\text{Valence}_i + \beta_2\text{Ambiguity}_i + \beta_3(\text{Valence}_i \times \text{Ambiguity}_i) + u_j + \epsilon_{ij}
\]

- `u_j` = random intercept for participant j (captures repeated measures).  
- **Robust SE** (Huber‑White) applied when any predictor is derived (FR‑001).  

### 3.2 Rigor & Corrections
- **Multiple Comparisons**: Benjamini‑Hochberg FDR applied to all fixed‑effect p‑values (FR‑004).  
- **Collinearity**: VIF computed for all fixed effects; VIF > 5.0 triggers `state/vif_flag.json` and suppresses claims of independent effects (FR‑005).  
- **Correlation Guard**: If Pearson r(Valence, Ambiguity) > 0.7, the interaction term is dropped and a warning is logged (preventing multicollinearity).  
- **Power Analysis**: Approximate a priori power using `statsmodels.stats.power.FTestPower` with assumed small‑to‑medium effect (f = 0.15), α = 0.05, power = 0.80 → required N ≈ 300 trials. If the post‑filter dataset falls below this, a “Power Limitation” flag is added to the PDF (SC‑002).  
- **Causal Framing**: All statements in the report are prefixed with “We observe an association …” per FR‑003.  

### 3.3 Derivation Strategy (Independent Measurement)
- **Valence**: `transformers` pipeline (`text-classification`) using `distilbert-base-uncased-emotion`. For images, a lightweight CNN (`torchvision.models.mobilenet_v3_small`) pretrained on FER‑2013; both run on CPU unless GPU fallback is triggered.  
- **Ambiguity**:  
  - **Text stimuli** – Lexical Ambiguity Index (frequency‑based word‑sense count from WordNet).  
  - **Image stimuli** – Texture variance computed via Laplacian filter (OpenCV).  
These derivations are **independent** of each other, satisfying the “no circular validation” requirement.

### 3.4 Sensitivity Analysis (FR‑006)
α‑levels: 0.01, 0.05, 0.10. For each α, the model’s fixed‑effect p‑values are re‑evaluated after FDR correction; results saved in `reports/sensitivity_analysis.csv` and visualized in the PDF.

## 4. Compute Feasibility & GPU Strategy
- **CPU‑first**: All preprocessing, VIF, LME fitting, and PDF generation run on the GitHub Actions runner (≤ 2 CPU cores, ≤ 7 GB RAM).  
- **GPU Escape Hatch**: If `derive_valence.py` detects that the transformer inference exceeds 30 seconds on CPU, it automatically switches to `device="cuda"` with 8‑bit quantization (`bitsandbytes`), executed on a free Kaggle GPU. The pipeline logs the switch; if the GPU run also fails, the step aborts with “Valence derivation unavailable”. No synthetic substitution is performed.

## 5. Decision Rationale
| Decision | Rationale |
|---|---|
| Conditional model equation | Guarantees reproducibility when demographics are missing (no imputation). |
| VIF before fitting | Prevents wasted compute on a collinear model; aligns with FR‑005. |
| FDR over Bonferroni | Retains statistical power for exploratory interaction tests while controlling family‑wise error. |
| GPU fallback only for valence derivation | Keeps the bulk of the pipeline CPU‑friendly; respects the hardware constraint. |
| Streaming verification with synthetic 8 GB file | Satisfies T040’s requirement to test > 7 GB streaming logic without exceeding CI disk limits (the synthetic file is generated, processed, then deleted). |
| Logging file creation (T009) | Guarantees `code/logs/pipeline.log` exists for auditability (addresses verifier feedback). |
| `pip.conf` with `--extra-index-url https://download.pytorch.org/whl/cpu` | Ensures `torch==2.3.0+cpu` installs deterministically (addresses T003a). |

---
