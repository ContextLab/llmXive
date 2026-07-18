# Annotation Protocol for Sentiment Validation

## Overview

This document defines the protocol for annotating comments to validate the VADER sentiment analysis tool against human judgments. This validation is critical for ensuring the reliability of sentiment measurements in the emotional contagion study.

## Annotation Requirements

### Annotator Count

- **Minimum**: 2 independent annotators must label each sampled comment.
- **Ideal**: 3 annotators per comment to enable more robust reliability metrics (e.g., Fleiss' Kappa).

### Annotation Labels

Annotators must assign one of the following labels to each comment:

- **positive**: The comment expresses positive sentiment, approval, or agreement.
- **negative**: The comment expresses negative sentiment, disapproval, or disagreement.
- **neutral**: The comment is factual, objective, or sentiment is ambiguous/unclear.

### Annotation Guidelines

1. **Read the full comment** in context if possible.
2. **Ignore sarcasm** unless it is explicitly clear (sarcasm is challenging and should be noted).
3. **Focus on the dominant sentiment** if multiple sentiments are present.
4. **When in doubt**, choose 'neutral' rather than forcing a positive/negative classification.
5. **Do not consider** the correctness of the argument, only the sentiment expressed.

### Sample Selection

- Comments are sampled from the validated dataset (`data/processed/valid_threads.csv`).
- A minimum of 100 comments should be annotated for statistical power.
- Sampling should be stratified by subreddit to ensure representation.

## Annotation Process

1. **Preparation**:
 - Select a representative subset of comments (see `code/data/sampling.py`).
 - Prepare the annotation file (`data/raw/annotations.json`).

2. **Annotation**:
 - Each annotator independently labels the comments.
 - Annotators should not communicate during the annotation process.
 - Time spent per comment should be recorded if possible.

3. **Aggregation**:
 - Combine annotations from all annotators.
 - Calculate inter-rater reliability (Cohen's Kappa for 2 annotators, Fleiss' Kappa for more).

4. **Validation**:
 - Compare human annotations with VADER predictions.
 - Calculate agreement metrics and confidence intervals.

## Data Storage

- **Raw annotations**: Stored in `data/raw/annotations.json`.
- **Validation report**: Generated in `data/processed/vader_validation_report.json`.
- **Justification**: Generated in `data/processed/validation_justification.json`.

## Quality Control

- **Inter-rater reliability**: Kappa must be ≥ 0.6 for acceptable agreement.
- **If Kappa < 0.6**:
 - Log a warning but do not halt the pipeline.
 - Review annotation guidelines for clarity.
 - Consider additional training for annotators.
- **Confidence intervals**: Bootstrapped 95% confidence intervals should be computed for Kappa to justify subset validity.

## Ethical Considerations

- Annotators should be informed about the purpose of the annotation task.
- No personally identifiable information (PII) should be shared with annotators.
- Annotator identities should be kept confidential.

## Version History

- **v1.0**: Initial protocol definition for PROJ-139.
- **Status**: Active for sentiment validation pipeline.
