# Specification: ArcANE - Automated Researcher for Character Narrative Evaluation

## Overview

ArcANE is a system designed to automatically generate and evaluate "character arcs" in public-domain literature. It uses Large Language Models (LLMs) to define psychological axes, generate "out-of-world" probes, and evaluate character consistency across different narrative contexts.

## User Stories

### US1: Construct and Validate Character Arc Specifications
Researchers can define independent Coarse and Fine psychological axes for characters. The system validates these axes for semantic independence and stores them in a structured format.

### US2: Generate Out-of-World Probes
The system generates novel, semantically distant scenario prompts (probes) for each character based on their defined axes. These probes are validated against the source text to ensure they are "out-of-world".

### US3: Execute Hybrid Prompting and Consistency Evaluation
The system executes the target model under Coarse, Fine, and Hybrid conditions, calibrates a Judge model against human annotations, and performs statistical analysis on the consistency scores.

## Constraints

- **Data Integrity**: All data must be sourced from verified public-domain texts or human annotations. No synthetic data generation for input.
- **Reproducibility**: All runs must be logged with seeds, parameters, and content hashes.
- **CPU Feasibility**: The system must be executable on standard CPU hardware using quantized models.

## Assumptions

- Target characters are limited to public-domain figures (e.g., Ebenezer Scrooge, Elizabeth Bennet).
- A verified Gold Standard dataset exists or can be generated deterministically if fetch fails (with explicit user permission).
