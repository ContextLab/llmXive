# Quickstart: The Impact of Subtle Linguistic Cues on Perceived Authenticity in AI Chatbots

## Prerequisites

- Python 3.11+  
- Git  
- 7 GB RAM, 14 GB disk (free-tier GitHub Actions runner)  
- Access to verified dataset URL (see `research.md` for gap note)

## Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. Create virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:  
   ```bash
   pip install -r code/requirements.txt
   python -m spacy download en_core_web_sm
   ```

## Data Preparation

### Step 1: Download Raw Data

The project requires a dataset with **human authenticity ratings**. As noted in `research.md`, the verified dataset (`MixSub-LLaMA-3.2`) lacks these ratings. **You must provide a verified dataset with human ratings before proceeding.**

If you have a verified dataset URL (e.g., from a published study), download it:

```bash
python src/utils/data_loader.py --url <VERIFIED_URL> --output data/raw/conversations.jsonl
```

> **Do NOT fabricate a URL.** If no verified dataset with human ratings exists, the pipeline cannot run.

### Step 2: Manual Annotation (If No Verified Dataset Exists)

If no verified dataset with human ratings exists, you must perform manual annotation:
1. Select a random sample of ≤10,000 conversations from `conversations.jsonl`.
2. Recruit human annotators and provide standardized instructions (1-5 Likert scale for authenticity).
3. Collect ratings in `data/processed/ratings.csv` with columns:
   - `conversation_id` (str)
   - `authenticity_score` (int, 1–5)
   - `rater_id` (str)
   - `annotation_instructions` (str)
4. Calculate Krippendorff's alpha (target ≥ 0.7) using the `krippendorff` library.

### Step 3: Extract Linguistic Features

Run the extraction script:

```bash
python src/extraction/main.py --input data/raw/conversations.jsonl --output data/processed/features.csv
```

This will:
- Calculate `pronoun_rate`, `hedge_density`, `valence_score`.  
- Skip empty/short texts (<5 words) and log exclusions.  
- Output `features.csv` with columns: `conversation_id`, `pronoun_rate`, `hedge_density`, `valence_score`, `length`, `turn_count`.

## Running the Analysis

### Correlation Analysis

```bash
python src/analysis/correlation.py --features data/processed/features.csv --ratings data/processed/ratings.csv --output data/derived/correlation_results.csv
```

Output includes:  
- Pearson and Spearman coefficients.  
- p-values and BH-corrected adjusted p-values.  
- Scatter plots (saved to `figures/`).

### Regression Analysis

```bash
python src/analysis/regression.py --features data/processed/features.csv --ratings data/processed/ratings.csv --output data/derived/regression_results.csv
```

Output includes:  
- Coefficients, standard errors, p-values.  
- Adjusted R², AIC.  
- VIF diagnostics.  
- Non-linearity test results.

## Generating the Report

```bash
python src/main.py --features data/processed/features.csv --ratings data/processed/ratings.csv --output data/derived/analysis_results.csv
```

This generates:
- `data/derived/analysis_results.csv` (final statistics).  
- `figures/` (correlation scatter plots, regression diagnostics).  
- `reports/associational_disclaimer.txt` (contains: "These results indicate association, not causation.").

## Validation

### Unit Tests

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Contract Tests

```bash
pytest tests/contract/
```

Ensure all contracts (schema validation) pass.

## Troubleshooting

- **Division by Zero**: Check `features.csv` for `excluded_reason = "empty_text"`.  
- **Missing Ratings**: Check log for exclusion count.  
- **Skewed Distributions**: Check `reports/diagnostics.txt` for Shapiro-Wilk flags.  
- **High VIF**: Check `reports/diagnostics.txt` for VIF >5 flags.  
- **Dataset Gap**: If no human ratings, the pipeline will fail at merge step; provide verified dataset or complete manual annotation.