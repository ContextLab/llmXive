# Implementation Plan: PROJ-050

## Objective
To determine if priming via negative sentiment exposure reduces prosocial actions in online comments.

## Methodology
1. **Data Collection**: Fetch Reddit comments from target subreddits.
2. **Classification**: Classify comments into "Prime" (negative sentiment) and "Control" groups based on lexical analysis with negation handling.
3. **Anonymization**: Hash user identifiers to ensure privacy.
4. **Scoring**: Calculate prosocial action counts and negative sentiment scores.
5. **Validation**: Compare automated scoring against human annotations.
6. **Analysis**: Fit Linear Mixed-Effects Models (LMM) to test the hypothesis.

## Key Constraints
- **Data Source**: Pushshift.io (Reddit archive).
- **Privacy**: SHA-256 hashing for user IDs; no raw timestamps in final output.
- **Reproducibility**: All scripts must be deterministic where possible; seeds set for random operations.
- **Hardware**: CPU-only execution required.

## Milestones
- **M1**: Data ingestion and classification pipeline complete.
- **M2**: Scoring and validation pipeline complete.
- **M3**: Statistical analysis and reporting complete.
