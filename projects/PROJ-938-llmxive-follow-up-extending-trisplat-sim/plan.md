# Project Plan: llmXive Follow-up - Extending TriSplat for CPU-only Edge Robotics

## Overview
This project extends the TriSplat architecture to run on CPU-only edge devices by replacing learned refinement heads with a differentiable geometry-only layer. The goal is to achieve feasible 3D scene reconstruction on standard 2-core CPUs within 30 minutes per scene.

## Objectives
1. Implement a CPU-feasible geometry-only reconstruction pipeline (US1)
2. Identify the minimum view count (sparsity threshold) for valid reconstruction (US2)
3. Benchmark latency and fidelity against the baseline TriSplat (US3)

## Scope
- **In Scope**: CPU-only execution, geometry-only layer, batch orchestration, statistical analysis, benchmark reporting
- **Out of Scope**: GPU acceleration, real-time video streaming, mobile deployment

## Technical Stack
- Python 3.11
- PyTorch (CPU mode)
- NumPy, SciPy, Scikit-learn
- RealEstate10K dataset (streaming)
- Trimesh for mesh generation

## Deliverables
1. `code/models/geometry_only.py`: Differentiable ray-surface intersection layer
2. `code/experiments/run_batch.py`: Batch orchestration engine
3. `data/processed/`: Benchmark results, threshold analysis, trade-off plots
4. `specs/001-llmxive-trisplat-ext/`: Documentation and contracts

## Timeline
- Phase 1: Setup (Week 1)
- Phase 2: Foundational (Week 1-2)
- Phase 3: US1 Implementation (Week 2-3)
- Phase 4: US2 Implementation (Week 3-4)
- Phase 5: US3 Implementation (Week 4-5)
- Phase 6: Stretch Goal & Polish (Week 5-6)

## Risk Mitigation
- **CPU Performance**: Use streaming dataset loading and aggressive downscaling (320x240)
- **Convergence**: Implement hard iteration limits and fallback placeholder meshes
- **Data Integrity**: Verify checksums for all downloaded dataset shards
