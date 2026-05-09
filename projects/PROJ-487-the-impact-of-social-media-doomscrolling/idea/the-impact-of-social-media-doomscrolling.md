---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Social Media “Doomscrolling” on Anticipatory Anxiety

**Field**: psychology

## Research question

How does the aggregate volume of negative news consumption on social media relate to population-level anticipatory anxiety during periods of global uncertainty?

## Motivation

Global events such as elections and pandemics have increased reliance on social media for news, often exposing users to negative cycles (“doomscrolling”). While existing research links this behavior to general distress, it remains unclear whether specific negative news exposure drives *anticipatory* anxiety (worry about future negative events) distinct from existential anxiety. Addressing this gap is critical for designing targeted mental health interventions and media literacy programs.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex using terms: "doomscrolling anxiety", "social media negative news anticipatory anxiety", and "news consumption anxiety correlation". Results were filtered for peer-reviewed or preprint studies published in the last 5 years.

### What is known

- [Doomscrolling and Existential Anxiety among Emerging Adults in Pakistan: Moderating Role of Cognitive Reappraisal (2025)](https://doi.org/10.37939/jnah.v3i04.198) — This study establishes a significant link between doomscrolling and *existential* anxiety, identifying cognitive reappraisal as a moderator.

### What is NOT known

Current literature does not distinguish between existential anxiety and *anticipatory* anxiety in the context of doomscrolling. There is no published work quantifying the specific relationship between aggregate negative news volume and indicators of future-oriented worry (anticipatory anxiety) using time-series data.

### Why this gap matters

Distinguishing between existential dread and anticipatory anxiety is vital for clinical practice; interventions for future-oriented worry differ from those for meaning-based distress. Filling this gap could inform platform design policies and public health messaging during crises.

### How this project addresses the gap

This project analyzes public time-series data to correlate negative news volume with anxiety-related search trends. By isolating keywords associated with *anticipatory* worry (e.g., "upcoming election anxiety", "future inflation worry"), we provide evidence on whether news consumption specifically predicts future-oriented anxiety states.

## Expected results

We expect a positive correlation between spikes in negative news volume and subsequent increases in anticipatory anxiety indicators, with a lag of 1-3 days. A null result would suggest that anticipatory anxiety is driven by factors other than immediate news exposure. Evidence will be confirmed via time-series regression with statistical significance (p < 0.05).

## Methodology sketch

- Download historical Google Trends data for anxiety-related keywords (e.g., "anticipatory anxiety", "worry about future") and negative news terms (e.g., "crisis", "disaster") using the `pytrends` Python library.
- Download public news volume data from the GDELT Project (Global Database of Events, Language, and Tone) for the same time period to cross-validate negative news exposure.
- Preprocess data: normalize time-series to z-scores, handle missing values via linear interpolation, and align timestamps to weekly intervals.
- Compute Pearson and Spearman correlation coefficients between news volume and anxiety indicators.
- Perform Granger causality tests to determine if news volume predicts future anxiety levels better than past anxiety levels.
- Visualize results using `matplotlib` (lag plots and correlation heatmaps).
- Run all analysis in a single Python script on GitHub Actions runners to ensure reproducibility within 6h runtime.

## Duplicate-check

- Reviewed existing ideas: None provided in context.
- Closest match: N/A.
- Verdict: NOT a duplicate
