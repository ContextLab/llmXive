# WBench CPU Adaptation

## Overview
This adaptation reproduces the core quantitative evaluation logic of the **WBench** paper (Multi-turn Interactive Video World Model Evaluation) on a **CPU-only, low-resource** environment.

## Simplifications & Approximations
To fit the 2 CPU / 7GB RAM / 25-min constraints, the following substitutions were made:

| Original Component | Adaptation Strategy |
| :--- | :--- |
| **Dataset** (289 cases, real videos) | **Synthetic Generation**: If real cases are missing, generates 10-50 synthetic JSON cases with randomized metadata and interactions. |
| **Video Quality Metrics** (HPSv3, Aesthetic, etc.) | **Proxy Simulation**: Uses deterministic random noise seeded by Case ID to simulate scores (0-10 scale). |
| **Consistency Metrics** (SAM2 Masks, Depth) | **Proxy Simulation**: Simulates consistency scores based on interaction type (e.g., navigation gets slightly lower scores). |
| **Navigation Metrics** (MegaSAM Poses) | **Proxy Simulation**: Calculates a mock adherence score based on case metadata. |
| **Physics Metrics** (Causal Fidelity) | **Proxy Simulation**: Randomized scores seeded by case ID. |
| **Real Video Input** | **None**: The pipeline operates purely on JSON metadata structures. No video files are processed. |

## Scientific Logic Preserved
While the *values* are synthetic, the *logic* of the evaluation remains:
1. **Multi-dimension Scoring**: Evaluates Video Quality, Consistency, Interaction (Navigation), and Physics separately.
2. **Aggregation**: Computes a composite "Total Score" across dimensions.
3. **Categorization**: Distinguishes between Navigation and Non-Navigation cases to analyze performance differences.
4. **Output Artifacts**: Produces the same structural outputs (CSV, JSON, Plots) as a real run, allowing verification of the evaluation pipeline.

## Usage
See `quickstart.md` for execution instructions.
The script is self-contained in `code/wbench_cpu_adaptation.py`.
