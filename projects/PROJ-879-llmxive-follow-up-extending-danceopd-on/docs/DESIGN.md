# Design Document

## Overview

This document outlines the design decisions for the llmXive follow-up project extending DanceOPD.

## Goals

- Generate a synthetic dataset of routing ground truth from the DanceOPD teacher model
- Train static decision trees to approximate the teacher's routing behavior
- Quantify fidelity degradation when using tree-predicted routing vs. teacher routing
- Perform statistical significance testing on the results

## Non-Goals

- Training new generative models
- Implementing GPU-specific optimizations (CPU-only execution)
- Real-time inference

## Design Decisions

### Data Generation

- **Source**: ImageNet-1K and LAION-400M via HuggingFace datasets
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to handle large datasets
- **Feature Extraction**: CLIP encoder for prompt embeddings
- **Teacher Inference**: Run on CPU with fallback logic for missing GPU artifacts

### Tree Training

- **Algorithm**: scikit-learn DecisionTreeClassifier
- **Depth Range**: Systematically vary `max_depth` from 2 to 20
- **Metric**: Routing Consistency (accuracy) against teacher labels

### Fidelity Evaluation

- **Image Generation**: Euler integrator with fixed step size
- **Metrics**: FID (torch-fidelity) and CLIP Score (transformers)
- **Comparison**: Tree-generated vs. Teacher-baseline images
- **Statistical Tests**: Bootstrap hypothesis test on FID, paired t-test on CLIP scores

### Error Handling

- **Timeout**: Hard 6-hour timeout using `signal.SIGALRM`
- **Partial Results**: Save intermediate results on timeout or early exit
- **Undefined Routes**: Exclude samples with invalid routing labels

## Data Contracts

All data artifacts must conform to the JSON schemas in `specs/contracts/`:
- `TeacherRoutingDataset.json`: Schema for the generated dataset
- `InferenceResult.json`: Schema for inference outputs
- `DecisionTreeMetadata.json`: Schema for trained tree metadata

## Performance Considerations

- **Memory**: Chunked loading to stay under 6 GB peak
- **Runtime**: 6-hour limit with partial result saving
- **Scalability**: Streaming data to avoid loading entire datasets into memory

## Future Work

- Implement parallel batch processing for image generation
- Optimize import statements to remove circular dependencies
- Add more unit tests for edge cases
