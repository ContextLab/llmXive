# Figures and Visualizations

## Figure 1: Preprocessing Pipeline Overview

**Description**: Flowchart showing the complete data processing pipeline from raw eye-tracking data to final regression results.

**Key Components**:
- Data ingestion and validation
- I-VT fixation detection
- ROI mapping
- Participant filtering
- Valence calculation
- Data merging
- Mixed-effects regression
- Robustness analysis

**Status**: To be generated from pipeline execution logs.

## Figure 2: Fixation Duration Distribution by ROI

**Description**: Histogram comparing fixation duration distributions for source_attribution vs. headline_body ROIs.

**Expected Pattern**: Bimodal distribution with distinct peaks for each ROI type.

**Data Source**: `data/derived/preprocessed_gaze.csv`

## Figure 3: Three-Way Interaction Effect

**Description**: Interaction plot showing the relationship between fixation duration, valence, and CRT scores on belief ratings.

**Axes**:
- X-axis: Fixation duration (ms)
- Y-axis: Belief rating
- Color: Valence (positive/negative)
- Panels: CRT score quartiles

**Expected Pattern**: Diverging lines indicating the three-way interaction effect.

**Data Source**: `data/derived/regression_results.csv`

## Figure 4: Robustness Threshold Sweep

**Description**: Line plot showing the stability of the three-way interaction coefficient across fixation duration thresholds (50ms, 100ms, 150ms).

**Axes**:
- X-axis: Fixation duration threshold (ms)
- Y-axis: Three-way interaction coefficient (β)
- Error bars: 95% confidence intervals

**Expected Pattern**: Stable coefficient with overlapping confidence intervals across thresholds.

**Data Source**: `data/derived/robustness_report.csv`

## Figure 5: Participant Exclusion Flowchart

**Description**: CONSORT-style flowchart showing participant inclusion/exclusion at each preprocessing stage.

**Stages**:
- Initial dataset
- After schema validation
- After fixation detection
- After ROI mapping
- After participant filtering
- Final sample

**Data Source**: `output/exclusion_log.txt`

## Figure 6: Valence Distribution by Lexicon

**Description**: Density plot comparing valence score distributions when using NRC vs. VADER lexicons.

**Expected Pattern**: Similar distributions with minor shifts at extreme values.

**Data Source**: `data/derived/valence_scores.csv`

## Figure 7: Random Effects Variance Components

**Description**: Bar chart showing variance explained by participant_id, headline_id, and residual error.

**Expected Pattern**: Significant variance at both participant and headline levels.

**Data Source**: `data/derived/regression_results.csv`

## Figure 8: Coefficient Recovery (Synthetic Data)

**Description**: Scatter plot comparing true coefficients (from synthetic data) vs. estimated coefficients.

**Expected Pattern**: Points along the diagonal line (y=x), indicating accurate recovery.

**Data Source**: `data/synthetic/ground_truth.csv` and `data/derived/regression_results.csv`

## Generation Instructions

To generate these figures:

1. **Install plotting dependencies**:
 ```bash
 pip install matplotlib seaborn
 ```

2. **Create a figure generation script** (e.g., `code/08_generate_figures.py`) that:
 - Loads the appropriate data files
 - Creates each figure using matplotlib/seaborn
 - Saves to `figures/` directory with descriptive filenames
 - Generates a summary report in `output/figure_report.txt`

3. **Example code structure**:
 ```python
 import matplotlib.pyplot as plt
 import seaborn as sns
 import pandas as pd

 # Load data
 df = pd.read_csv('data/derived/regression_results.csv')

 # Create interaction plot
 plt.figure(figsize=(10, 6))
 sns.lineplot(data=df, x='fixation_duration', y='belief_rating',
 hue='valence', style='crt_quartile')
 plt.savefig('figures/interaction_effect.png')
 ```

## Figure File Naming Convention

- `figures/01_pipeline_overview.png`
- `figures/02_fixation_duration_distribution.png`
- `figures/03_three_way_interaction.png`
- `figures/04_robustness_threshold_sweep.png`
- `figures/05_exclusion_flowchart.png`
- `figures/06_valence_distribution.png`
- `figures/07_variance_components.png`
- `figures/08_coefficient_recovery.png`

## Figure Resolution and Format

- **Resolution**: 300 DPI for publication quality
- **Format**: PNG for figures, PDF for vector graphics
- **Color scheme**: Accessible color palettes (colorblind-friendly)
- **Font size**: Minimum 10pt for readability

## Integration with Paper

Each figure should be referenced in the relevant paper section:
- Figure 1: Methods section
- Figures 2-3: Results section
- Figure 4: Robustness section
- Figure 5: Data Quality section
- Figures 6-8: Supplementary materials

## Future Work

1. Add animated visualizations of attention patterns over time
2. Create interactive dashboards for exploring the regression results
3. Generate heatmaps showing fixation density across headline text
4. Produce Sankey diagrams showing participant flow through exclusion criteria