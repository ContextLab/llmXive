# Annotation Protocol for Sentiment Validation

## 1. Overview
This document defines the protocol for human annotation of Reddit comments to validate the VADER sentiment analysis tool. The goal is to establish a ground truth dataset against which automated sentiment scores can be compared.

## 2. Annotation Scale
Annotators will use a **5-point Likert scale** to rate the sentiment of each comment:
- **1**: Very Negative
- **2**: Somewhat Negative
- **3**: Neutral / Mixed
- **4**: Somewhat Positive
- **5**: Very Positive

## 3. Instructions for Annotators
1. **Read the Context**: Read the full thread context (parent post and immediate parent comment) to understand the conversation flow.
2. **Read the Target**: Read the specific comment to be annotated.
3. **Ignore Personal Bias**: Do not let your personal agreement or disagreement with the content influence the sentiment rating. Focus on the emotional tone (anger, joy, sadness, etc.) and the intensity of the expression.
4. **Handle Sarcasm**: If sarcasm is evident and reverses the literal meaning, annotate the *intended* sentiment, not the literal words.
5. **Handle Ambiguity**: If the sentiment is truly ambiguous or mixed, select **3 (Neutral)**.

## 4. Sampling Strategy
To ensure the validation set is representative, we employ **stratified random sampling** based on:
- **Thread Length**: Quartiles of the number of comments in the thread.
- **VADER Sentiment Proxy**: Quartiles of the initial VADER compound score calculated on the raw text.

This creates a 2x2 grid (Length x Sentiment) to ensure coverage of short/long threads and negative/positive sentiment extremes, as well as the middle ground.

## 5. Data Storage
- Raw annotations are stored in `data/raw/annotations.json`.
- The file is checksummed (SHA-256) upon creation to ensure integrity.
- The format includes `comment_id`, `annotator_id`, `sentiment_score` (1-5), and `timestamp`.

## 6. Quality Control
- **Inter-Rater Reliability**: A subset of comments will be annotated by multiple annotators. Cohen's Kappa will be calculated.
- **Threshold**: If Cohen's Kappa < 0.6, the annotation session is paused for retraining.

## 7. Fallback Protocol
If human annotations cannot be gathered (e.g., due to budget or time constraints), the project will attempt to load a public sentiment corpus (e.g., from HuggingFace datasets like `sentiment140` or `emotion`) to serve as a proxy for validation. If neither human annotations nor a public corpus are available, the validation report will be marked as `unvalidated`.
