# Data Model: llmXive Follow-up: Physics-Teacher Distillation

## Overview
The project manipulates three primary data entities:

1. **PhysicsTrajectory** – deterministic state‑vector sequence produced by Box2D.
2. **VideoSequence** – rendered 16‑frame MP4 aligned with a PhysicsTrajectory.
3. **EvaluationResults** – per‑sequence metrics and aggregated statistical outputs, **including** an optional `trajectory_pixel_corr` field for the student‑frame TPC metric.

All entities are versioned, checksummed, and validated against the contracts below. The **VideoSequence** schema is defined in `contracts/video_sequence.schema.yaml` and is enforced during data generation (see T1.2). Every metric value in `EvaluationResults` is a real measurement traced through `outputs/manifest.json` (Anti‑Fabrication Commitment); no placeholder values are permitted in any field.

## Data Flow Diagram (textual)

```
Box2D metadata (generated internally) → generate.py → PhysicsTrajectory (.npz) + VideoSequence (.mp4)
Training loader (student) reads both → student_diffusion.py → student checkpoint
Neural‑teacher baseline loader reads the SAME physics data → neural_teacher.py → baseline checkpoint
Evaluation/metrics.py consumes videos + trajectories → per‑sequence EvaluationResults (real measurements)
Statistical analysis aggregates EvaluationResults → JSON/CSV reports
outputs/manifest.json records provenance (script, input checksums, seed) for every output file
```

All intermediate files are stored under `data/` (raw) or `outputs/` (derived) and referenced by checksum in the manifest.

---

