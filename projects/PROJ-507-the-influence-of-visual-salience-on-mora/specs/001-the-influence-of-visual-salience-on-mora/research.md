# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Research Question
Does increasing the visual salience (via luminance contrast/brightness) of a target object in a morally ambiguous scenario significantly increase the blame attributed to that object by observers?

## Theoretical Background
Visual salience drives attentional capture. In moral psychology, the "focalist" hypothesis suggests that attention to an agent increases the perceived responsibility for an outcome. This study tests whether manipulating low-level visual features (salience) causally alters high-level moral judgments (blame).

## Dataset Strategy

### Primary Verified Datasets
The project relies on the following verified dataset for the primary visual stimuli. This dataset contains the necessary semantic content (social scenarios) required to test the hypothesis.

- **Visual Genome**: `https://homes.cs.washington.edu/~ranjay/visualgenome/data/dataset.json` (or verified HuggingFace mirror `visual_genome`).
  - **Usage**: Serves as the source for base scenarios. The dataset contains images of scenes with associated object and relationship annotations.
  - **Selection Criteria**: We will programmatically filter for scenarios containing "social conflict" or "accident" keywords in the metadata to narrow the candidate pool. **Note**: Visual Genome does not inherently contain "morally ambiguous" labels. Therefore, the project will not rely on dataset metadata alone for this property.
  - **Validation**: To ensure construct validity, a **mandatory human coding step** (FR-008) will be performed on this subset. Two independent annotators will label selected images as 'morally ambiguous'. Only scenarios achieving ≥80% inter-rater reliability (Cohen's κ ≥ 0.8) will be included in the final stimulus set. Ambiguity is NOT assumed from dataset creators; it is empirically validated by the study's protocol. **The pilot phase IS this human coding run.**

### Secondary References
The following datasets are cited for methodological reference or code validation only and are NOT used for primary stimuli or core statistical analysis of the research question.

- **ANOVA Reference Data**: `https://huggingface.co/datasets/P2SAMAPA/p2-etf-functional-anova-results/resolve/main/functional_anova_2026-05-19.json`
  - **Usage**: Used strictly for unit-testing the statistical pipeline (e.g., verifying that the `statsmodels` ANOVA implementation produces expected output formats on synthetic data). It is not used for the actual hypothesis testing.
- **CPU-only Text Data**: `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet`
  - **Usage**: Referenced only for potential metadata extraction logic or text-based filtering scripts if needed. It is not used for visual stimuli or behavioral analysis.

## Methodology

### Experimental Design
- **Design**: Within-subject, repeated-measures design.
- **Independent Variable**: Visual Salience (3 levels: Low, Medium, High).
- **Dependent Variable**: Blame Rating (1-7 Likert scale).
- **Participants**: Real recruited pilot cohort (N=20-30).
- **Procedure**:
  1. Ingest images from the verified Visual Genome dataset.
  2. **Human Coding**: Recruit annotators to label a subset of images for moral ambiguity (FR-008). Exclude non-ambiguous scenarios.
  3. Generate multiple variants per valid image (Low, Med, High salience) using PIL.
  4. Present variants in randomized order to the pilot cohort.
  5. Collect blame ratings.

### Statistical Analysis Plan
1. **Data Cleaning**: Exclude straight-liners (FR-007).
2. **Assumption Checking**:
   - Normality of residuals (Shapiro-Wilk).
   - Sphericity (Mauchly's test). If violated, apply Greenhouse-Geisser or Huynh-Feldt correction (FR-004).
3. **Primary Test**: Repeated-measures ANOVA (FR-004) on real pilot data.
   - Null Hypothesis ($H_0$): No difference in mean blame ratings across salience levels.
   - Alternative Hypothesis ($H_1$): At least one salience level differs.
4. **Post-hoc Tests**: Bonferroni-corrected pairwise t-tests (FR-005).
   - Comparisons: Low vs. Medium, Medium vs. High, Low vs. High.
   - Correction: Adjust $\alpha$ to $0.05 / 3 \approx 0.0167$.
5. **Effect Size**: Calculate partial eta-squared ($\eta_p^2$) and 95% Confidence Intervals (FR-006).

### Power & Sample Size
- **Assumption**: Medium effect size ($f = 0.25$).
- **Limitation**: Pilot study may be underpowered. The analysis will explicitly report power limitations and wider CIs if $N$ is small (Edge Case).

## Decision Rationale

### Why CPU-only?
The project is constrained to GitHub Actions free-tier runners with limited CPU and RAM resources. Deep learning models for image generation or analysis are infeasible. `Pillow` provides sufficient control for luminance manipulation without GPU requirements.

### Why Human Coding for Pilot?
Construct validity requires that the "morally ambiguous" label is empirically validated, not assumed. The pilot *is* the human coding run (FR-008) to ensure the dependent variable (blame in an ambiguous context) is real and not synthetic. This resolves the risk of circular validation and ensures the dataset matches the research question's semantic requirements.

### Why Bonferroni?
With only 3 pairwise comparisons, Bonferroni is appropriate and conservative (Assumption). It controls the family-wise error rate (SC-003).

### Why Real Data (Not Simulation)?
Using simulated or placeholder images fails construct validity because moral ambiguity is a semantic property of complex scenes. The analysis must be performed on real behavioral data from real participants responding to real stimuli to answer the research question. The pilot is an empirical test, not a code validation simulation.

## Limitations
- **Dataset**: The pilot relies on a small, manually curated subset of the Visual Genome dataset.
- **Power**: Small sample size may limit detection of small effects.
- **Generalizability**: Pilot results are preliminary; full study requires larger N and broader image diversity.