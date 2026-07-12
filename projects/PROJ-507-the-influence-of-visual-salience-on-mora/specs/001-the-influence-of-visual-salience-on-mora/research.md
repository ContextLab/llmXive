# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview

This research investigates whether enhancing visual salience (via luminance contrast/brightness) in morally ambiguous scenarios systematically influences blame judgments. The study employs a within-subject experimental design where participants rate blame for the same scenario under low, medium, and high salience conditions. The hypothesis is that higher visual salience increases perceived blame, independent of semantic content. The analysis utilizes **Linear Mixed-Effects Models (LMM)** to account for the nested structure of the data (responses within participants and scenarios), avoiding pseudoreplication.

## Dataset Strategy

### Primary Dataset: Visual Genome

**Source**: Visual Genome is an open dataset containing images with region-level annotations, including object, attribute, and relationship labels. It includes social and conflict scenarios suitable for moral ambiguity identification.

**Verified URL**: Visual Genome is accessed via its official website: **https://visualgenome.org/**. The dataset does not have a standard HuggingFace `datasets` loader for the full image+annotation set. The project will download a canonical subset (images and JSON annotations) manually via HTTP fetch from the official site, verify checksums, and store in `data/raw/`. This approach ensures reproducibility and adheres to the 'Verified Accuracy' principle.

**Relevance**: 
- Contains images with social/conflict metadata (FR-008) for initial candidate filtering.
- Provides region-level annotations to identify target objects for salience manipulation.
- Open access aligns with reproducibility principles.

**Limitations**:
- Does **not** contain pre-labeled 'moral ambiguity' or 'blame' ground truth.
- Requires a two-stage filtering process: (1) metadata filtering for 'social' or 'conflict' tags, followed by (2) a dedicated **Human Coding** step to generate the 'ambiguous' label.
- Image quality and target object clarity may vary; some images may fail manipulation (Edge Case 1).

### Secondary Dataset: CLIP Model for Semantic Validation

**Source**: CLIP (Contrastive Language-Image Pre-training) model from OpenAI, available via HuggingFace `transformers` library.

**Verified URL**: The model weights are hosted on HuggingFace (https://huggingface.co/openai/clip-vit-base-patch32). The model is loaded via `transformers` without external URL citation (as it is a pre-trained model, not a dataset).

**Relevance**:
- Validates that salience manipulation preserves global semantic content (FR-001).
- Computes cosine similarity between original and manipulated image embeddings (target ≥0.95).

**Limitations**:
- CLIP is a general-purpose model, not a psychometric tool for detecting subtle semantic shifts in moral ambiguity.
- A high CLIP score does not guarantee that the *moral* narrative remains constant.
- **Mitigation**: Complement CLIP with Structural Similarity Index (SSIM) calculated on **non-target regions** to ensure only the target region's salience is altered. Additionally, pixel-level metrics (`contrast_change`) are used to verify the manipulation itself.

### Alternative Datasets (Not Used)

- **ANOVA (json)**: https://huggingface.co/datasets/P2SAMAPA/p2-etf-functional-anova-results/resolve/main/functional_anova_2026-05-19.json — Not relevant (functional analysis results, not visual stimuli).
- **CLIP (csv)**: https://huggingface.co/datasets/CodedotAI/code-clippy-tfrecords/resolve/main/tfrecords/test/checkpoint.txt — Not relevant (code dataset).
- **CPU-only (parquet)**: https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet — Not relevant (text-only dataset).

**Decision**: Only Visual Genome is suitable for visual stimuli; CLIP and SSIM are used for validation (not as datasets). No other verified datasets are applicable.

## Methodology

### Phase 1: Stimulus Generation & Human Coding

1. **Metadata Filtering**: Download Visual Genome subset; filter images with "social" or "conflict" tags (FR-008).
2. **Human Coding (New Step)**: 
   - Present filtered images to ≥2 independent annotators.
   - **Rating Scale**: Coders rate 'moral ambiguity' on a **1-7 Likert scale** (1=Not ambiguous at all, 7=Highly ambiguous) with specific instructions to focus on the presence of **conflicting moral cues**.
   - Calculate Cohen's κ. Scenarios with κ ≥0.6 and mean ambiguity score in the mid-range (3-5) are labeled 'morally ambiguous' (FR-008).
   - Scenarios failing consensus are excluded.
3. **Manipulation Check (Pilot)**: 
   - Run `03_manipulation_check.py` to verify that the intended salience levels (low/medium/high) result in **perceptually distinct** luminance/contrast values.
   - This pilot task ensures that the manipulation is effective before the main survey. If the pilot fails, adjust contrast parameters.
4. **Salience Manipulation**: For each ambiguous scenario:
   - Identify target object (via region annotations or manual selection).
   - Generate three variants: low (baseline), medium (enhanced contrast), high (enhanced contrast).
   - Verify semantic preservation via CLIP (cosine similarity ≥0.95) AND SSIM on non-target regions (FR-001).
   - Exclude variants failing validation (Edge Case 1).

**Rationale**: Two-stage filtering ensures ambiguity; Human Coding operationalizes the construct; Manipulation Check ensures perceptual validity; CLIP+SSIM isolates salience from semantic changes.

### Phase 2: Survey Deployment

1. **Within-Subject Design**: Each participant rates all scenarios at all salience levels (randomized order) (FR-002).
2. **Blame Rating**: 1-7 Likert scale (1=not at all blameworthy, 7=extremely blameworthy) (FR-003).
3. **Data Collection**: Record participant ID, image ID, salience level, timestamp (FR-003).

**Rationale**: Within-subject design controls for individual differences; randomization prevents order effects.

### Phase 3: Data Cleaning

1. **Straight-Lining Detection**: Flag participants with identical ratings across all items (FR-007).
2. **Exclusion**: Remove flagged responses; report exclusion rate (SC-004).

**Rationale**: Ensures data validity; prevents noise from inattentive participants.

### Phase 4: Statistical Analysis

1. **Linear Mixed-Effects Model (LMM)**: 
   - Model: `Blame ~ Salience + (1 | Participant) + (1 | Scenario)` (FR-004).
   - **Note**: LMM is used instead of standard Repeated-Measures ANOVA to account for the nested data structure (responses within scenarios) and avoid pseudoreplication.
   - Checks: Convergence status; residual normality.
   - **Robustness**: If normality assumptions are violated (Likert scale), switch to **Friedman test** (non-parametric alternative) or ordinal LMM.
2. **Post-Hoc Comparisons**: Bonferroni-corrected t-tests for pairwise contrasts (low vs. medium, medium vs. high, low vs. high) (FR-005).
3. **Effect Sizes**: Calculate marginal/conditional R-squared and 95% CIs (FR-006, SC-002, SC-005).

**Rationale**: LMM accounts for nested data (participants, scenarios), preventing pseudoreplication. Corrections control family-wise error rate.

## Statistical Rigor

### Multiple Comparison Correction
- **Method**: Bonferroni correction (α_corrected = 0.05 / 3 comparisons = 0.0167).
- **Justification**: Small number of planned comparisons (3); Bonferroni is conservative but appropriate (Assumption 7).

### Power Analysis
- **Target**: Detect medium effect size (η² = 0.06) with power = 0.80, α = 0.05.
- **Sample Size**: ~100-200 participants (within-subject design increases power).
- **Limitation**: With only ~20-60 scenarios, the **effective sample size** for the fixed effect of 'Salience' is constrained by the number of **scenarios**, not participants. If the effect varies by scenario (which is likely in moral psychology), the study may be underpowered to detect a generalizable effect. The LMM treats 'Scenario' as a random effect to account for this, but this limitation is explicitly reported if sample falls below threshold.

### Causal Inference
- **Design**: Within-subject experiment with controlled manipulation.
- **Assumptions**: Randomization of salience levels; no confounding visual features (Assumption 6).
- **Claims**: Causal effect of salience on blame (if significant); otherwise, associational.

### Measurement Validity
- **Blame Scale**: 1-7 Likert validated in moral psychology literature (Assumption 2).
- **Semantic Validation**: CLIP cosine similarity ≥0.95 AND SSIM on non-target regions ensure manipulation does not alter meaning or introduce artifacts (FR-001).
- **Manipulation Validity**: `03_manipulation_check.py` ensures perceptual distinctness of salience levels.

### Predictor Collinearity
- **Salience Levels**: Orthogonal manipulation (low, medium, high); no definitional collinearity.
- **Reporting**: Descriptive statistics for each level; no independent effects claimed.

### Robustness Checks
- **Normality**: If residuals are non-normal (Likert scale), switch to **Friedman test** or ordinal LMM.
- **Convergence**: If LMM fails to converge, use robust standard errors or simplify random effects structure.

## Compute Feasibility

- **CLIP Inference**: ~60 images × 3 variants = 180 images; CPU inference in the range of seconds per image → A short duration total (well within 6h limit).
- **LMM**: <200 participants × 60 stimuli = <12,000 data points; analysis <30 minutes on CPU.
- **Memory**: <7GB RAM; images processed in batches; no large models loaded.

**Decision**: All methods are CPU-tractable; no GPU required.

## Ethical Considerations

- **Participant Privacy**: Anonymize participant IDs; no PII stored.
- **Data Security**: Encrypt survey responses; store in `data/` with checksums.
- **Informed Consent**: Simulated survey includes consent form (for real deployment).

## Limitations

1. **Dataset Availability**: Visual Genome may lack sufficient ambiguous scenarios; scope may need adjustment.
2. **CLIP Validation**: May not capture all semantic changes; SSIM and human pilot check used as safeguards.
3. **Sample Size**: Power may be limited if recruitment falls below target; report limitations explicitly.
4. **Generalizability**: Results apply to simulated scenarios; real-world moral judgments may differ.
5. **Scenario Constraint**: The number of scenarios limits the generalizability of the effect across different types of moral dilemmas.
6. **Ordinal Data**: Likert scale data may violate normality assumptions; non-parametric fallback planned.

## References

- Visual Genome: https://visualgenome.org/ (open dataset; accessed via official site).
- CLIP Model: https://huggingface.co/openai/clip-vit-base-patch32 (pre-trained model; loaded via `transformers`).
- Statistical Methods: `statsmodels` and `pingouin` documentation for LMM, Mauchly's test, Bonferroni correction.