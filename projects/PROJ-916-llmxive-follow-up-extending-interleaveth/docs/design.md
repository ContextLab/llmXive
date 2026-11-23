# Design Documents

## Overview

llmXive is an automated science pipeline designed to evaluate agentic interleaved generation
against structured scene descriptions. The project simulates the "grounding gap" using a
text-based simulator and evaluates performance via an agentic loop (Planner, Generator, Critic).

## Architecture

### Components

1. **Simulator** (`src/simulator`):
 - Converts text prompts into structured JSON.
 - Injects controlled noise to simulate uncertainty.
 - Validates spatial relationships.

2. **Agents** (`src/agents`):
 - **Planner**: Determines intent and next steps.
 - **Generator**: Reconstructs scene descriptions using an LLM.
 - **Critic**: Evaluates outputs and provides feedback.

3. **Pipeline** (`src/pipeline`):
 - Orchestrates the agentic loop.
 - Manages memory and timeouts.
 - Logs trajectory states.

4. **Stats** (`src/stats`):
 - Calculates metrics (error rates, F1-scores).
 - Performs statistical analysis (t-tests, effect sizes).
 - Generates reports.

5. **Data** (`src/data`):
 - Loads real datasets (WISE, RISE, etc.) via streaming.
 - Ensures data integrity via checksums.

## Key Decisions

- **Real Data Only**: All loaders must fail loudly if core datasets are missing.
- **CPU Tractability**: Optimized for CPU execution with memory limits (~7GB).
- **Modularity**: Each user story is independently implementable and testable.

## Contracts

- `SceneGraph`: Structured representation of scene objects and relationships.
- `TrajectoryLog`: Log of intermediate states and critiques.

## References

- `specs/001-llmxive-interleave-structure-vs-modality/`: Detailed design specifications.
