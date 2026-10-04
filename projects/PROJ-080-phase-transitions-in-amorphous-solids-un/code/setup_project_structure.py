import os
from pathlib import Path

def main():
    """
    Create the project directory structure and initial schema files for
    PROJ-080-phase-transitions-in-amorphous-solids-un.
    """
    # Define the project root. In the actual deployment, this is the repo root.
    # We use the current working directory to ensure we operate within the project tree.
    project_root = Path(".")

    # Directories to create (relative to project root)
    # Note: T001a specifies these directories under `projects/PROJ-...` but the
    # execution context and other tasks (T001b, T002, etc.) imply a flat structure
    # at the repo root (e.g., `data/raw`, `code/`). We follow the convention of
    # the existing completed tasks which use `data/`, `code/`, etc. at the root.
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state",
    ]

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Schema files to create
    schema_files = [
        {
            "path": "specs/contracts/trajectory.schema.yaml",
            "content": """
# Trajectory Data Schema
# Defines the structure for raw and processed MD trajectory data
# This schema is static and does not store dynamic checksums.

$schema: "http://json-schema.org/draft-07/schema#"
title: MD Trajectory Data
type: object
description: Schema for amorphous solid shear trajectory data

properties:
  metadata:
    type: object
    properties:
dataset_id:
  type: string
  description: Unique identifier for the dataset source
source:
  type: string
  description: Origin of the data (e.g., HuggingFace, Synthetic)
strain_rate:
  type: number
  description: Applied strain rate (1/s)
temperature:
  type: number
  description: Temperature of the simulation (K)
particle_count:
  type: integer
  minimum: 1
  description: Total number of particles in the simulation box
box_dimensions:
  type: array
  items:
    type: number
  minItems: 3
  maxItems: 3
  description: Box dimensions [Lx, Ly, Lz]
timestamp:
  type: string
  format: date-time
  description: Creation timestamp

  frames:
    type: array
    items:
type: object
properties:
  timestep:
    type: integer
    minimum: 0
  stress_tensor:
    type: array
    items:
      type: number
    minItems: 6
    maxItems: 6
    description: [Sxx, Syy, Szz, Sxy, Sxz, Syz]
  positions:
    type: array
    items:
      type: array
      items:
        type: number
      minItems: 3
      maxItems: 3
    description: Particle positions [x, y, z]
  velocities:
    type: array
    items:
      type: array
      items:
        type: number
      minItems: 3
      maxItems: 3
    description: Particle velocities [vx, vy, vz]
  labels:
    type: array
    items:
      type: string
      enum: ["brittle", "ductile", "unknown"]
    description: Classification label if available

required:
  - metadata
  - frames

additionalProperties: false
"""
        },
        {
            "path": "specs/contracts/output.schema.yaml",
            "content": """
# Output Data Schema
# Defines the structure for processed analysis outputs

$schema: "http://json-schema.org/draft-07/schema#"
title: Analysis Output Data
type: object
description: Schema for processed metrics and predictions

properties:
  precursor_metrics:
    type: array
    items:
type: object
properties:
  particle_id:
    type: integer
  timestep:
    type: integer
  d2_min:
    type: number
    minimum: 0
  local_shear_strain:
    type: number
  shear_band_id:
    type: integer
    minimum: 0
required:
  - particle_id
  - timestep
  - d2_min

  yield_flags:
    type: object
    properties:
trajectory_id:
  type: string
yielding_timestep:
  type: integer
  minimum: 0
is_indeterminate:
  type: boolean
stress_drop_percentage:
  type: number
confidence:
  type: number
  minimum: 0
  maximum: 1
    required:
- trajectory_id
- yielding_timestep
- is_indeterminate

  statistical_results:
    type: object
    properties:
test_type:
  type: string
  enum: ["permutation", "ks_test"]
observed_statistic:
  type: number
p_value:
  type: number
  minimum: 0
  maximum: 1
corrected_p_value:
  type: number
  minimum: 0
  maximum: 1
is_significant:
  type: boolean
sample_size:
  type: integer
  minimum: 1
note:
  type: string
  description: Any amendments or methodological notes

  prediction_results:
    type: object
    properties:
threshold:
  type: number
confusion_matrix:
  type: object
  properties:
    tp:
      type: integer
    tn:
      type: integer
    fp:
      type: integer
    fn:
      type: integer
f1_score:
  type: number
  minimum: 0
  maximum: 1
fpr:
  type: number
  minimum: 0
  maximum: 1
fnr:
  type: number
  minimum: 0
  maximum: 1
validation_split_size:
  type: integer

required:
  - precursor_metrics
  - yield_flags

additionalProperties: false
"""
        }
    ]

    for file_info in schema_files:
        file_path = project_root / file_info["path"]
        with open(file_path, "w") as f:
            f.write(file_info["content"])
        print(f"Created file: {file_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()