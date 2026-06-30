# Data Model: Reproduce & Validate EmbFilter

## Overview

This document defines the data structures used in the reproduction pipeline, focusing on the input dataset schema, the intermediate embedding representation, and the final output report schema.

## Input Data Model

The input data consists of sentence pairs and ground truth similarity scores.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `sentence1` | string | The first sentence in the pair. | MTEB STS dataset |
| `sentence2` | string | The second sentence in the pair. | MTEB STS dataset |
| `score` | float | Ground truth similarity score (a continuous scale). 

The research question is: Can large language models accurately assess the semantic similarity of scientific abstracts? The method is: We will compare LLM-generated similarity scores to human-annotated similarity scores using Pearson correlation. (Wang et al., 2023) [https://doi.org/10.1101/2023.08.11.5522893] | MTEB STS dataset |
| `id` | string | Unique identifier for the pair. | MTEB STS dataset |

## Intermediate Data Model (Embeddings)

The `EmbFilter` transformation produces two sets of embeddings for each sentence pair.

| Field | Type | Description | Dimensions |
| :--- | :--- | :--- | :--- |
| `embedding_baseline` | tensor | Raw embeddings from the LLM unembedding layer. | [N, D] (e.g., 4096) |
| `embedding_filtered` | tensor | Embeddings after applying the frequency-based linear filter. | [N, D] or [N, D'] if reduced |
| `filter_params` | dict | Parameters used for the filter (threshold, dimension). | N/A |

## Output Data Model

The final output is a structured JSON report containing the performance metrics and metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique identifier for the execution run. |
| `model_name` | string | Name of the LLM used. |
| `dataset_name` | string | Name of the benchmark dataset. |
| `sample_size` | int | Number of samples processed. |
| `baseline_score` | float | Spearman correlation of baseline embeddings. |
| `filtered_score` | float | Spearman correlation of filtered embeddings. |
| `delta` | float | Difference (filtered - baseline). |
| `improvement_claimed` | boolean | True if `delta > 0` (or within negligible margin). |
| `methodology_note` | string | Explicit statement of "Associational Analysis". |
| `parameters` | dict | Log of frequency threshold and other hyperparameters. |
| `timestamp` | string | ISO 8601 timestamp of the run. |
