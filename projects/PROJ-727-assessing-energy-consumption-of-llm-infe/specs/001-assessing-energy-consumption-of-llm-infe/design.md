# Design Document: Assessing Energy Consumption of LLM Inference

## Overview
This document outlines the design for assessing the energy consumption of LLM inference for code completion tasks.

## Objectives
- Quantify energy-to-token metrics for GPT-2-small, CodeBERT, and StarCoder-1B.
- Perform statistical analysis of energy vs. model size.
- Generate sustainability trade-off visualizations.

## Constraints
- CPU-only execution.
- No GPU quantization.
- StarCoder-1B used instead of StarCoder-base.

## Data Sources
- HumanEval dataset from GitHub.
- CodeCarbon for energy tracking.

## Deliverables
- Energy metrics CSV.
- Statistical analysis report.
- Visualization plots.
