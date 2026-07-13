# Research: The Impact of Text Message Tone on Perceived Emotional Support

## 1. Research Question & Hypotheses

**Primary Question**: Does the relationship between paralinguistic features (emoji, punctuation, length) and perceived emotional support vary depending on the sender's relationship to the recipient (close friend vs. acquaintance)?

**Hypotheses**:
- **H1 (Interaction)**: There is a significant interaction between Relationship Type and specific paralinguistic features. Specifically, high cue intensity (e.g., multiple emojis, exclamation marks) will increase perceived support more for acquaintances than for close friends.
- **H2 (Main Effects)**: Specific features (e.g., emojis) may have main effects on perceived support independent of relationship.
- **H3 (Non-Linearity)**: The effect of emojis may be non-linear (e.g., 2 emojis may not be twice as effective as 1).

## 2. Dataset Strategy

Since the study requires a controlled experimental design with specific manipulations of emoji, punctuation, and length, **no external public dataset** is suitable. The "Verified datasets" block provided (POPE, RefCOCO, MP-DocVQA) contains image-text pairs for VQA tasks and is irrelevant to this text-message sentiment study.

**Strategy**:
1.  **Stimulus Generation (FR-001)**: A Python script will generate a factorial design of text messages.
    -   *Base Scenarios*: 4 generic scenarios (e.g., "I had a rough day").
    -   *Factors*:
        -   Emoji Level: 3 levels (None, 1 Emoji, 2+ Emojis).
        -   Punctuation Level: 2 levels (Standard, Exaggerated/Repeated).
        -   Length Level: 2 levels (Concise, Elaborate).
    -   *Total Variants*: 4 scenarios × 3 × 2 × 2 = 48 unique stimuli.
2.  **Data Simulation (FR-002)**: A second script will simulate human ratings.
    - *Participants*: Simulated N = [deferred] (targeting [deferred] power for medium interaction effect, α=0.05).
    - *Design*: Within-subjects. Each participant rates all 48 stimuli in both "Friend" and "Acquaintance" contexts.
    - *Simulation Modes*:
        -   **Effect Present**: Ratings drawn from a distribution with a mean shift based on the hypothesized interaction.
        -   **Null Hypothesis (Validation)**: Ratings drawn with NO interaction effect (only main effects or noise) to verify the pipeline correctly returns non-significant results (Type I error control).
        -   **Noise Only**: Pure random noise to test robustness.
    - *Validity*: This synthetic approach allows for exact control over the independent variables, which is necessary for the factorial analysis required by the spec. The inclusion of Null/Noise modes ensures the pipeline is not validated in a tautological loop.

**Dataset Variables**:
-   `stimulus_id`: Unique ID for the text variant.
-   `participant_id`: Unique ID for the rater.
-   `relationship`: Categorical (Friend, Acquaintance).
-   `emoji_level`: Integer (0, 1, 2).
-   `punctuation_type`: Categorical (Standard, Exaggerated).
-   `length_category`: Categorical (Concise, Elaborate).
-   `rating`: Integer 1-7 (Perceived Emotional Support).

## 3. Statistical Analysis Plan

### 3.1 Primary Model (FR-003)
-   **Method**: Linear Mixed-Effects Model (LMM) using `statsmodels` or `linearmodels` (CPU-only).
-   **Formula**: `rating ~ relationship * emoji_level * punctuation_type * length_category + (1 | participant_id) + (1 | stimulus_id)`
    -   **Encoding**: Categorical factors (Emoji, Punctuation, Length) will be **dummy-coded (treatment contrasts)**. This avoids assuming a linear additive effect (e.g., that 2 emojis are exactly twice as intense as 1) and allows the model to estimate the specific effect of each level.
-   **Degrees of Freedom**: Satterthwaite approximation (standard in `lmerTest` equivalent for Python).
-   **Outcome**: Fixed effect estimates, standard errors, t-values, and p-values for the **interaction terms** (e.g., `relationship:emoji_level`, `relationship:punctuation_type`).

### 3.2 Post-Hoc Analysis (FR-004)
-   **Condition**: If any interaction term is statistically significant (p < 0.05).
-   **Method**: Tukey-corrected pairwise comparisons.
-   **Implementation**: `statsmodels.stats.multicomp` or `pingouin` (CPU-optimized).
-   **Correction**: Family-wise error rate controlled at α = 0.05.

### 3.3 Factorial Decomposition & Construct Validity
-   **Objective**: Address the concern that a composite "cue_intensity" variable may mask specific psychological mechanisms.
-   **Procedure**:
    1.  Run the full factorial model (Section 3.1) to test individual factors and their interactions.
    2.  Analyze the specific interaction terms (e.g., `relationship:emoji_level`) to determine if the effect is driven by emojis, punctuation, or their combination.
    3.  This step validates that the findings are not artifacts of an arbitrary weighting scheme.

### 3.4 Sensitivity Analysis (FR-005)
-   **Objective**: Test robustness of the interaction effect to the *definition* of "Cue Intensity" (structural, not just mathematical).
-   **Procedure**:
    1.  Define 3 alternative **structural** operationalizations of "High Cue":
        -   *Model A (Disjunctive)*: High cue = (Emoji > 0) OR (Punctuation = Exaggerated).
        -   *Model B (Conjunctive)*: High cue = (Emoji > 0) AND (Punctuation = Exaggerated).
        -   *Model C (Dominant)*: High cue = Emoji > 0 (ignoring punctuation/length).
    2.  Create a binary "High_Cue" variable for each model and re-run the LMM: `rating ~ relationship * High_Cue + (1|participant) + (1|stimulus)`.
    3.  Compare the interaction p-values and effect sizes across the three models.
-   **Success Metric**: The interaction effect remains significant (p < 0.05) across all three structural definitions, demonstrating robustness of the psychological finding. This tests if the finding holds across different *logical* definitions of the construct, rather than just mathematical weights.

### 3.5 Data Quality & Cleaning (FR-006)
-   **Straight-lining Detection**: Calculate variance of ratings per participant across all stimuli. If variance = 0, flag and exclude.
-   **Missing Data**: Listwise deletion for participants with missing ratings > 10%.
-   **Randomization Check**: Verify that `relationship` assignment is balanced. If not, exclude affected participants.

## 4. Compute Feasibility & Constraints

-   **Hardware**: GitHub Actions Free Tier (2 vCPU, 7 GB RAM, No GPU).
-   **Library Choice**: `statsmodels` and `linearmodels` are pure Python/Cython, fully CPU-compatible. No `torch` or GPU-specific libraries are used.
- **Data Size**: 48 stimuli × ~200 participants × 2 contexts = [deferred] rows. < 1 MB. Trivial for RAM.
-   **Runtime**: LMM on <20k rows typically completes in < 30 seconds. Sensitivity analysis (3x runs) < 2 minutes. Well within 6-hour limit.

## 5. Decision Rationale

-   **Synthetic Data vs. Real Data**: Real data collection via Prolific is outside the scope of the *computational pipeline* implementation. The spec requires the *system* to be capable of collecting and analyzing data. Simulating the data allows the pipeline to be fully tested and verified (FR-002 acceptance criteria) without external dependencies or costs.
-   **Full Factorial LMM**: Essential for handling the crossed random effects and testing the specific psychological mechanism (interaction of specific cues) without assuming linearity.
-   **Null Hypothesis Simulation**: Critical for validating the pipeline. If the pipeline only simulates "effect present" data, it cannot verify its ability to correctly return null results.
-   **Structural Sensitivity**: Tests whether the finding is robust to *how* we define "high cue" (e.g., does it matter if we require both emoji and punctuation, or just one?), which is more psychologically meaningful than re-weighting a linear sum.