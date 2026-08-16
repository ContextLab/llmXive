# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Background and Rationale

Visual salience—the perceptual prominence of stimuli—may influence moral judgments by directing attention to specific elements in ambiguous scenarios. This study tests whether enhancing luminance contrast/brightness in target regions of morally ambiguous images increases blame ratings. The hypothesis is grounded in attentional capture theories, where salient features disproportionately influence decision-making.

## Dataset Strategy

| Dataset | Purpose | Source (Verified URL) | Access Method | Notes |
|---------|---------|------------------------|---------------|-------|
| **MoralD** | Primary source of morally ambiguous scenarios | **NO verified source found** (do NOT cite URL) | Use `datasets.load_dataset("moral_d", split="train", streaming=True)` if available; otherwise, use verified synthetic generation pipeline. | MoralD is a text-based moral dilemma dataset. If an image subset is not available, the plan switches to a 'Synthetic Scenario Generation' pipeline using a verified text-to-image model (e.g., Stable Diffusion) with verified prompts to generate the required visual stimuli. |
| CLIP embeddings | Semantic similarity validation | **NO verified source found** | Use `transformers` library for on-the-fly embedding extraction; no precomputed dataset needed | Ensure CPU feasibility; if GPU required, offload to Kaggle with scaled subset. |
| Moral Intent Classifier | Moral narrative preservation validation | **NO verified source found** | Use a pre-trained BERT model (e.g., `bert-base-uncased` fine-tuned on moral dilemma descriptions) for on-the-fly scoring | Ensure CPU feasibility; if GPU required, offload to Kaggle with scaled subset. |
| Synthetic survey data | Pilot testing | N/A | Generate programmatically with `pandas` | Validate pipeline before real deployment. |

**Critical Note on Dataset Availability**: The spec requires "open visual datasets" but no verified URL is provided for Visual Genome or a direct image-based MoralD subset in the verified datasets block. The plan must rely on open subsets accessible via Hugging Face or direct download, with explicit acknowledgment of potential gaps. If MoralD lacks a direct image subset, the plan **explicitly switches** to a 'Synthetic Scenario Generation' pipeline using a verified text-to-image model (e.g., Stable Diffusion) with verified prompts, acknowledging this as a necessary pivot to ensure construct validity. This avoids the infeasible approach of manual selection from millions of images in general datasets like Visual Genome. For this plan, we assume a subset of MoralD is available via `datasets.load_dataset("moral_d", ...)` or a synthetic generation pipeline is used.

**Decision/Rationale**:
- **CPU-first**: All image processing (Pillow), statistical analysis (statsmodels), and CLIP/BERT embedding extraction (transformers on CPU) are planned for CPU. CLIP/BERT extraction may be slow; if GPU offload is triggered, the same code runs on Kaggle with `device="cuda"`.
- **Data Feasibility**: If MoralD lacks direct moral annotations, the plan explicitly states that human coding (FR-008) is mandatory to identify ambiguous scenarios. No synthetic data replaces real images unless the image generation pipeline is the primary source.

## Methodological Approach

### Phase 0: Pilot Power Analysis (New)

1. **Pilot Data Collection**: Run a small pilot (N=10 participants, 10 scenarios) using the synthetic or open dataset.
2. **Variance Estimation**: Calculate the variance of blame ratings and the effect size (f) from the pilot data.
3. **Sample Size Calculation**: Use the pilot variance to calculate the required sample size for the full study to achieve adequate statistical power. If the pilot suggests a medium effect size (f=0.15), the full study will target N=60 participants.
4. **Gate**: The full study cannot proceed without a power calculation based on these pilot estimates.

### Phase 1: Data Preparation and Salience Manipulation (FR-001, FR-008)

1. **Ingest Images**: Stream MoralD subset (or alternative open dataset/synthetic pipeline) using `datasets.load_dataset(..., streaming=True)`. Filter candidates via metadata tags ('dilemma', 'conflict').
2. **External Ground Truth Validation (Task-008)**: Fetch a pre-validated list of 'morally ambiguous' scenario IDs from a verified external source (e.g., a specific HuggingFace dataset or a published benchmark) and cross-reference the selected scenarios against this list. If the external source is unavailable, use a 'Synthetic Ground Truth' generation step using a verified prompt library. This ensures the 'ingest' step is a retrieval, not a new data collection study.
3. **Human Coding (FR-008)**: Script `02_human_coding.py` (simulated or integrated) collects ≥3 independent ratings per scenario on a 5-point ambiguity scale. Compute mean score and Cohen's κ; retain scenarios with mean ≥3.5 and κ ≥0.6. **Note**: Human coding is used for *confirmation* of the pre-selected scenarios, not for *definition* of the ambiguity pool.
4. **Salience Manipulation**: For each ambiguous scenario, generate low/medium/high salience variants by adjusting luminance contrast/brightness in target regions (defined by bounding box). Validate with:
   - CLIP cosine similarity ≥0.95 (original vs. manipulated).
   - RMS contrast change ≥15% in ROI.
   - Texture/edge density change <0.05.
   - **Moral Intent Preservation**: A pre-trained BERT model scores the 'moral narrative' of the image description before and after manipulation. The manipulation is retained only if the correlation between pre- and post-manipulation intent scores is ≥0.90.

**Statistical Rigor**:
- **Multiple Comparisons**: Bonferroni correction for pairwise salience contrasts (multiple comparisons).
- **Sample Size**: Power analysis mandatory (Phase 0); full study ≥60 participants based on pilot variance.
- **Causal Inference**: Experimental design (within-subject manipulation) supports causal claims; confounds controlled via semantic integrity checks.
- **Measurement Validity**: CLIP embeddings and BERT intent classifier validated against human ratings; ambiguity scale cross-referenced with external framework (e.g., MoralD).
- **Collinearity**: Not applicable (salience is independently manipulated).

### Phase 2: Survey Deployment and Data Collection (FR-002, FR-003)

1. **Balanced Randomization (Task-002)**: Present salience variants in a Latin Square design. A script generates a Latin Square for the 3 salience levels and assigns each participant a row. This ensures balanced order across the participant pool.
2. **Blame Ratings**: 1-7 Likert scale (1=Not at all blameworthy, 7=Extremely blameworthy).
3. **Data Storage**: Record participant ID, image ID, salience level, timestamp.

**Feasibility**: Survey simulated for pilot; real deployment via Prolific/university pool. Data collected in CSV/SQLite.

### Phase 3: Statistical Analysis and Reporting (FR-004, FR-005, FR-006)

1. **Data Cleaning (FR-007)**: Exclude straight-liners (variance <0.1 or >90% identical ratings).
2. **CLMM Analysis**: Model blame ratings with fixed effect of salience, random intercepts for Participant and Scenario. Check convergence; switch to robust alternative (e.g., LMM with bootstrap) if needed.
3. **Fallback to Wilcoxon**: If CLMM fails to converge and LMM is not suitable, the system MUST switch to a **Wilcoxon signed-rank test with Bonferroni correction** as mandated by FR-005. The results of this fallback test will be stored in the `wilcoxon_results` array in the output schema.
4. **Post-hoc Comparisons**: Tukey-adjusted tests for salience pairs (low vs. medium, etc.).
5. **Effect Sizes**: Odds ratios with 95% confidence intervals (Type III Sums of Squares).
6. **Power Analysis**: Post-hoc G*Power equivalent; flag if power <0.80.
7. **Precision Check**: Compare the confidence interval width against the pre-registered threshold defined in `config/pre_registration.yaml`.

**Statistical Rigor**:
- **Multiple Comparisons**: Bonferroni/Tukey correction applied.
- **Power**: Acknowledge limitations if sample size insufficient.
- **Causal Claims**: Justified by experimental design.
- **Measurement Validity**: Blame scale validated against literature.
- **Collinearity**: Not applicable.

## Edge Cases and Mitigations

- **Image Manipulation Failure**: Log failures; exclude from analysis.
- **Straight-lining Participants**: Exclude based on variance/identical rating thresholds.
- **Low Sample Size**: Report reduced power; widen confidence intervals.
- **CLMM Convergence Failure**: Switch to robust alternative (LMM/bootstrap) OR Wilcoxon signed-rank test as per FR-005.

## Limitations

- **Dataset Availability**: MoralD may lack direct moral annotations; human coding is mandatory for confirmation.
- **CPU Feasibility**: CLIP/BERT extraction may be slow; offload to Kaggle if needed.
- **Power**: Pilot study may lack power; full study design mitigates this.