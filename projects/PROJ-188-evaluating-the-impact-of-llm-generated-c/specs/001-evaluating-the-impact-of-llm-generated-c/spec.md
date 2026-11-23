# Spec: Evaluating the Impact of LLM-Generated Code Explanations

## User Stories

### US1: Dataset Curation and Explanation Generation
As a researcher, I want to curate a dataset of code snippets with complexity labels and generate LLM explanations so that I can use them in my study.

### US2: Study Survey Construction and Deployment
As a researcher, I want to construct a survey with three conditions (Code Only, Code+LLM, Code+Docstring) and randomize participants so that I can collect valid comprehension data.

### US3: Statistical Analysis and Robustness Reporting
As a researcher, I want to analyze the survey data using LMM and report BLEU sensitivity so that I can draw valid conclusions about the impact of LLM explanations.

## Functional Requirements

- FR-001: System must use CodeLlama-7B for explanation generation (with TinyLlama fallback).
- FR-005: Analysis must use LMM with participant-only random intercepts.
- FR-009: Report must include limitation statement about BLEU similarity.

## Data Model

- Snippet: {snippet_id, code, docstring, complexity_score, complexity}
- Response: {participant_id, condition, snippet_id, answer, latency_ms, timestamp}
- Analysis Result: {threshold, accuracy_mean, latency_mean, p_value_interaction}