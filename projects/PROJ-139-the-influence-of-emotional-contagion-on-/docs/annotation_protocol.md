# Annotation Protocol for Sentiment Validation

## Purpose
This document defines the protocol for human annotation of comment sentiment to validate the VADER sentiment analysis tool against human judgment. This validation is a critical component of the Constitution Principle VII, ensuring that automated sentiment scores align with human interpretation.

## Annotation Scale
Annotators will use a **5-point Likert scale** to rate the sentiment of each comment:

| Score | Label | Description |
|:--- |:--- |:--- |
| -2 | Very Negative | Strongly negative sentiment, hostility, or severe criticism. |
| -1 | Negative | Negative sentiment, criticism, or disagreement. |
| 0 | Neutral | No clear sentiment, factual statement, or mixed feelings that cancel out. |
| +1 | Positive | Positive sentiment, agreement, or praise. |
| +2 | Very Positive | Strongly positive sentiment, enthusiasm, or strong agreement. |

## Instructions for Annotators
1. **Context**: Read the full thread context if necessary to understand the nuance, but focus primarily on the specific comment being rated.
2. **Tone**: Pay attention to sarcasm, irony, and emotional intensity. VADER is designed to handle these, but human judgment is the ground truth.
3. **Neutrality**: If a comment is purely informational without emotional coloring, mark it as Neutral (0).
4. **Mixed Sentiment**: If a comment contains both positive and negative elements, judge the *overall* dominant sentiment. If perfectly balanced, mark as Neutral (0).
5. **Confidence**: Annotators should mark comments they are unsure about for a secondary review, but still provide their best estimate.

## Sampling Strategy
- **Source**: Comments are sampled from the dataset downloaded in T008 (`data/raw/reddit_threads.jsonl`).
- **Method**: Stratified random sampling to ensure representation across different subreddits and initial sentiment ranges (as estimated by a preliminary VADER run).
- **Size**: Target N = 200 comments for initial validation.
- **Constraint**: If human annotation data is unavailable, the system will fall back to a pre-validated corpus from HuggingFace (e.g., `nltk_data/sentiment/sentiment_corpus.json`) as defined in the implementation script.

## Data Storage
- Raw annotations will be stored in `data/raw/annotations.json`.
- The file will be checksummed (SHA-256) upon creation to ensure integrity.
- Format: JSON list of objects containing `comment_id`, `text`, `annotator_id`, `score`, and `timestamp`.

## Reliability Check
- If multiple annotators rate the same comment, Inter-Rater Reliability (Cohen's Kappa) will be computed.
- A Kappa score < 0.6 will trigger a warning but will not halt the pipeline (per task T007b requirements).

## Version
- Protocol Version: 1.0
- Last Updated: 2023-10-27
