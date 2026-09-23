# llmXive Follow-up: Extending TriSplat for CPU-only Edge Robotics

**Project ID**: PROJ-938-llmxive-follow-up-extending-trisplat-sim
**Status**: Active

## Overview
This project implements a CPU-feasible geometry-only 3D reconstruction pipeline
extending the TriSplat architecture. It targets edge robotics scenarios where
GPU resources are unavailable, focusing on explicit geometric constraints to
achieve valid mesh reconstruction within strict time and memory budgets.

## Features
- CPU-only inference (2-core affinity)
- Geometry-only differentiable ray-surface intersection
- Dynamic view count support (2-5 views)
- RealEstate10K streaming dataset integration
- Automated batch orchestration with timeout handling
- Statistical analysis for sparsity threshold identification

## Structure
- `code/` - Python implementation
- `data/` - Dataset and processed artifacts
- `tests/` - Unit and integration tests
- `specs/` - Design documents and specifications
- `state/` - Project state and artifact hashes

## Quickstart
See `specs/001-llmxive-trisplat-ext/quickstart.md` for detailed setup and execution instructions.

## License
Research use only.
