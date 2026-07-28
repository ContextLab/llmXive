# Research: The Impact of Text Message Tone on Perceived Emotional Support

## 1. Research Question & Hypotheses

**Primary Question**: Does the interaction between sender relationship type (close friend vs. acquaintance) and paralinguistic cue intensity (emoji, punctuation, length) significantly predict perceived emotional support in text messages?

**Hypotheses**:
- **H1**: Cue intensity (high emoji/punctuation/length) will increase perceived emotional support for messages from close friends more than for messages from acquaintances (Interaction Effect).
- **H2**: The effect of cue intensity will be non-linear (inverted-U); excessive cues may be perceived as insincere for acquaintances but appropriate for friends.

## 2. Dataset Strategy

The project requires a dataset of text stimuli and human ratings. Since the specification involves a *new* experimental design (specific factorial combinations of emoji/punctuation/length in specific relational contexts), no existing public dataset contains this exact data.

**Strategy**:
1.  **Stimulus Generation**: We will generate the stimuli programmatically using a factorial design (3 emoji levels × 2 punctuation levels × 2 length levels × [N] base scenarios). This ensures exact control over the independent variables.
2.  **Rating Data**:
    *   **CI/Development (Validation Only)**: We will use a **simulated dataset** (`data/raw/simulated_ratings.csv`) that mimics the expected distribution of human ratings (Likert 1-7) with added noise. This allows the pipeline to be tested for reproducibility and statistical correctness (does the code run?) without requiring external API keys (Prolific) or manual data collection during the CI build. **These results are NOT reported as findings.**
    *   **Real Data (Scientific Findings)**: The pipeline is designed to accept a CSV from a Prolific study. The `04_collect_real_data.py` script handles Prolific API calls. The final paper relies **solely** on `data/raw/real_ratings.csv`.

**Dataset Verification**:
No external verified dataset URL exists for this specific experimental design. The verified datasets listed in the project context (MME, GQA, NLVR2) are for computer vision and multimodal reasoning, not text message tone analysis. Therefore, **we do not cite any external dataset URL**. We rely on the **generated data** (stimuli) and **collected data** (ratings) as the primary source, which is fully reproducible via the `code/` scripts.

| Component | Source | Access Method | Justification |
|-----------|--------|---------------|---------------|
| Stimuli | `code/01_generate_stimuli.py` | Programmatic Generation | No existing dataset matches the specific factorial design. |
| Simulated Ratings | `code/02_simulate_ratings.py` | Programmatic Simulation | Used for CI validation only. Does not support empirical claims. |
| Real Ratings | `code/04_collect_real_data.py` | Prolific API / Manual CSV | Required by FR-002 for empirical validity. |
| Power Analysis | `code/01_power_analysis.py` | Simulation-based (Literature) | Standard practice for LMM power analysis (Bates et al.) using literature effect sizes. |

## 3. Statistical Methodology

**Primary Model**: Linear Mixed-Effects Model (LMM)
- **Fixed Effects**: Relationship Type (Friend/Acquaintance), Cue Intensity (Continuous), Cue Intensity² (Quadratic term for H2), Interaction (Relationship × Cue Intensity).
- **Random Effects**: Random intercepts for `Participant_ID` and `Stimulus_ID` to account for repeated measures.
- **Distribution**: Gaussian (Likert 1-7 treated as continuous approximation, standard in psychometrics for N > 30).
- **Estimation**: Restricted Maximum Likelihood (REML).
- **Degrees of Freedom**: Satterthwaite approximation (using `statsmodels` or `lmerTest` equivalent).
- **Implementation**: `statsmodels` (Python) is the primary SSoT. `rpy2` is excluded to ensure CI compatibility.

**Multiple Comparison Correction**:
- If the interaction is significant, post-hoc pairwise comparisons will be performed.
- Correction: Tukey's HSD (Honestly Significant Difference) to control Family-Wise Error Rate (FWER).

**Sensitivity Analysis**:
- We will re-run the LMM with three alternative definitions of "Cue Intensity", anchored to pilot literature (e.g., emoji intensity scales):
    1.  **Equal Weight**: Emoji=1, Punctuation=1, Length=1.
    2.  **Emoji-Biased**: Emoji=2, Punctuation=0.5, Length=0.5 (based on literature suggesting emoji dominate tone).
    3.  **Punctuation-Biased**: Emoji=0.5, Punctuation=2, Length=0.5.
- **Metric**: Stability of the interaction p-value and effect size (Cohen's f²) across these definitions.

**Robustness Checks**:
- **Straight-lining**: Participants with zero variance across all stimuli will be flagged and excluded (FR-006).
- **Missing Data**: Listwise deletion for participants with >20% missing ratings.

## 4. Compute Feasibility

- **CPU-First**: The LMM implementation uses `statsmodels` (Python), which is CPU-optimized. No GPU acceleration is required or available.
- **Memory**: The dataset (N [deferred] rows) fits comfortably within 7 GB RAM.
- **Time**: The full pipeline (generation + power analysis + simulation + real collection logic + LMM + sensitivity) is estimated to run in < 30 minutes on a 2-core runner (excluding real data collection time).

## 5. Decision Rationale

**Why Simulation?**
Real data collection via Prolific is a *research* step, not a *CI* step. The CI pipeline must demonstrate that the code works. Using a simulated dataset that adheres to the statistical assumptions of the LMM allows us to verify the pipeline's correctness (reproducibility) without incurring costs or waiting for human subjects. The `02_simulate_ratings.py` script generates data with known parameters, allowing us to verify that the LMM recovers the expected interaction effect (**Pipeline Correctness**). **This does not validate the hypothesis (Scientific Validity).** The simulation is a tool to ensure the code is bug-free before running on real data.

**Why No External Dataset?**
The verified datasets (MME, GQA, NLVR2) are irrelevant to this specific psychological question. Inventing a URL or forcing a fit with a vision dataset would violate the "Fabrication" and "Verified Accuracy" gates. The correct approach is to generate the data required by the experimental design.

**Why Power Analysis?**
Arbitrary sample sizes (e.g., "500") risk underpowered or overpowered studies. A formal power analysis using literature-derived effect sizes ensures the study is designed to detect the effect if it exists, satisfying FR-002.

**Why Quadratic Terms?**
H2 posits a non-linear relationship (inverted-U). A standard linear interaction assumes monotonicity. Adding a quadratic term allows the model to detect curvilinear effects, improving scientific soundness.