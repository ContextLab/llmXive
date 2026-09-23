# Project Plan: Extending TriSplat for CPU-only Edge Robotics

## Objective
Extend the TriSplat 3D reconstruction framework to operate on CPU-only edge devices
by replacing learned refinement heads with explicit geometric constraints.

## Scope
- Replace GPU-dependent components with CPU-compatible alternatives
- Implement differentiable ray-surface intersection using local geometry
- Optimize for 2-core CPU execution with <6GB RAM usage
- Identify minimum view count for valid reconstruction

## Constraints
- Must run on standard 2-core CPU (edge robotics hardware)
- Maximum 30 minutes per scene reconstruction
- Maximum 6 hours for full batch (N=20-50 scenes)
- Must handle monocular input gracefully (skip with warning)
- No synthetic data; must use RealEstate10K streaming

## Success Criteria
1. Valid mesh output (.obj/.ply) from CPU-only pipeline
2. Identification of sparsity threshold (min views for convergence)
3. Quantitative comparison with baseline TriSplat (latency vs. fidelity)
4. Reproducible results with deterministic sampling

## Milestones
1. **Setup**: Project structure and dependencies (Phase 1)
2. **Foundation**: Core utilities, data loaders, and metrics (Phase 2)
3. **US1**: CPU-feasible geometry-only reconstruction (Phase 3)
4. **US2**: Sparsity threshold identification (Phase 4)
5. **US3**: Benchmarking and trade-off analysis (Phase 5)
6. **Polish**: N=50 stretch goal and reproducibility hardening (Phase 6-7)

## Dependencies
- TriSplat base model weights (frozen)
- RealEstate10K dataset (streaming)
- Python 3.11+, PyTorch (CPU), NumPy, SciPy, Trimesh
