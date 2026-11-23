# Specification: InterleaveThinker - Reinforcing Agentic Interleaved Generation

## Overview

This specification defines the design for llmXive, an automated science pipeline that evaluates agentic interleaved generation against single-pass baselines.

## Problem Statement

Current vision-language models struggle with complex scene understanding due to the "grounding gap" between text prompts and visual reality. This project aims to:
1. Simulate this gap using a text-based simulator
2. Implement an agentic loop to iteratively refine scene descriptions
3. Quantify the improvement over single-pass approaches

## Design Goals

- **Deterministic**: Text-based simulator must be reproducible
- **CPU-tractable**: All experiments must run on CPU within 6 hours
- **Real data**: No synthetic data for core datasets (WISE, RISE)
- **Modular**: Components must be independently testable

## Components

1. **Simulator**: Generates structured JSON from text prompts with controllable noise
2. **Agentic Loop**: Planner → Generator → Critic iterative refinement
3. **Metrics**: Graph Edit Distance, F1-score, statistical significance
4. **Pipeline**: Orchestrates data loading, simulation, and analysis

## Constraints

- RAM: ≤ 7GB during execution
- Runtime: ≤ 6 hours
- Data: Real datasets only (WISE, RISE)

## Success Criteria

- Simulator error rate within 5-15% in Noisy Mode
- Agentic loop completes within time/memory constraints
- Statistical analysis shows significant improvement over baseline

## References

- InterleaveThinker: Reinforcing Agentic Interleaved Generation
- Visual Genome, GQA, WISE, RISE datasets
