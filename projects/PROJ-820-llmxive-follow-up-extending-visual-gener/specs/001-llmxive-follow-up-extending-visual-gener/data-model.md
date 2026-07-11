# Data Model: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

## 1. Overview
This document defines the data structures used in the `llmXive-followup` project. All data is stored in local files under `data/`. The model is designed for reproducibility and strict schema validation.

## 2. Entities & Relationships

### 2.1 SceneDescription
The raw input text describing a visual scene.
- **Attributes**: `scene_id`, `description_text`, `created_at`.
- **Source**: Curated by researcher.

### 2.2 PhysicsConstraint
The machine-readable representation of physics rules derived from `pymunk`.
- **Attributes**: `scene_id`, `constraints_json` (JSON object), `validity_flag` (boolean), `contradiction_detected` (boolean).
- **Relationship**: One-to-One with `SceneDescription`.

### 2.3 Prompt
The text string used for image generation.
- **Attributes**: `prompt_id`, `scene_id`, `group` (baseline/experimental/control), `prompt_text`.
- **Relationship**: One-to-One with `SceneDescription` (Experimental/Control groups include descriptors).

### 2.4 GeneratedImage
The output image file.
- **Attributes**: `image_id`, `prompt_id`, `group`, `seed`, `file_path`, `generation_status` (success/failure).
- **Relationship**: One-to-One with `Prompt`.

### 2.5 ViolationInstance
The result of the geometric evaluation.
- **Attributes**: `image_id`, `detected_objects` (list of boxes), `violation_type` (floating/interpenetration/none), `violation_flag` (boolean), `confidence_score` (float).
- **Relationship**: One-to-One with `GeneratedImage`.

### 2.6 AggregatedResult
The statistical summary.
- **Attributes**: `group`, `total_count`, `violation_count`, `violation_rate`, `confidence_interval`.
- **Relationship**: Aggregated from `ViolationInstance`.

## 3. File Formats

### 3.1 Input: `data/raw/scene_descriptions.csv`
- **Format**: CSV
- **Columns**: `scene_id`, `description_text`

### 3.2 Intermediate: `data/derived/physics_constraints/{scene_id}.json`
- **Format**: JSON
- **Schema**: See `contracts/physics-constraint.schema.yaml`

### 3.3 Intermediate: `data/derived/prompts/{prompt_id}.txt`
- **Format**: Text
- **Content**: Single line prompt string.

### 3.4 Intermediate: `data/derived/generated_images/{image_id}.png`
- **Format**: PNG (512x512)

### 3.5 Output: `data/derived/evaluation_results/{image_id}.json`
- **Format**: JSON
- **Schema**: See `contracts/evaluation-result.schema.yaml`

### 3.6 Final: `data/processed/final_analysis.csv`
- **Format**: CSV
- **Columns**: `metric`, `baseline_value`, `experimental_value`, `control_value`, `p_value`, `significance`

## 4. Data Flow
1. `SceneDescription` -> `PhysicsConstraint` (via `physics_engine.py`)
2. `SceneDescription` + `PhysicsConstraint` -> `Prompt` (via `prompt_engine.py`)
3. `Prompt` -> `GeneratedImage` (via `diffusion_runner.py`)
4. `GeneratedImage` + `PhysicsConstraint` -> `ViolationInstance` (via `detector.py`)
5. `ViolationInstance` -> `AggregatedResult` (via `statistics.py`)

## 5. Data Hygiene Rules
- **Immutability**: Raw data (`scene_descriptions.csv`) is never modified.
- **Checksums**: All files in `data/derived/` and `data/processed/` are checksummed (SHA-256) upon creation.
- **PII**: No personally identifiable information is stored.
- **Versioning**: File names include `scene_id` and `prompt_id` to ensure traceability.