---
action_items:
- id: 971b6f5728fc
  severity: science
  text: 'Reorganize the entire project structure to match plan.md: Create src/, src/configs/,
    src/inference/, src/scripts/, src/tests/, contracts/, results/, and outputs/ directories.
    Move requirements.txt to the root (if not already) and ensure all source code
    is inside src/.'
- id: 81d6c3d2097a
  severity: science
  text: Implement the missing inference.py and inference_sp.py scripts inside src/inference/
    as defined in tasks.md (T019, T022) to handle video generation, replacing the
    current longlive_quant_benchmark.py which does not fulfill the spec's video generation
    requirement.
- id: 94a041494efe
  severity: science
  text: Create the required contract schemas (contracts/inference_output.schema.yaml
    and contracts/metrics_report.schema.yaml) as defined in tasks.md (T006, T007)
    to enable automated validation of outputs.
- id: 8f1ec9f2d663
  severity: science
  text: 'Generate the required artifacts: Execute the corrected pipeline to produce
    a valid video file in outputs/ and a results/metrics.json file conforming to the
    new schema, replacing the current benchmark CSV/JSON which do not meet the spec''s
    success criteria (SC-002, SC-003).'
- id: e5621c3f85f4
  severity: science
  text: Update README.md and docs/reproducibility/ to reflect the new directory structure
    and provide accurate instructions for running the src/inference/inference.py script
    on a CPU-only runner.
artifact_hash: ab9711753b9f1eb5efc4087472f3f059632b14199733f097bce70aa0af425f8b
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/specs/001-https-arxiv-org-abs-2605-18739/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-30T12:24:16.491105Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: full_revision
---

The project exhibits a critical structural disconnect between the defined specification/plan and the actual filesystem layout, rendering the work irreproducible and non-compliant with the research scope.

**1. Missing Spec-Defined Directory Structure**
The `plan.md` explicitly defines a project structure where source code resides in `src/`, configurations in `src/configs/`, and contracts in `contracts/` (or `specs/.../contracts/`).
- **Defect**: The actual filesystem root contains `longlive_quant_benchmark.py` and `requirements.txt` at the root level. The `src/` directory, `inference/` subdirectory, and `contracts/` directory are entirely missing.
- **Impact**: The project fails to organize code as planned, making it impossible to locate the `inference.py` or `inference_sp.py` scripts required by `FR-003` and `FR-007`.

**2. Missing Core Artifacts and Output Directories**
The `spec.md` (User Story 2) and `plan.md` (Phase 1) mandate the generation of a video artifact (`.mp4`/`.webm`) and a structured metrics report (`results/metrics.json`).
- **Defect**: The `outputs/` and `results/` directories do not exist. The only artifacts produced are `data/quant_benchmark_results.csv`, `data/quant_benchmark_summary.json`, and `figures/quant_benchmark_comparison.png`.
- **Impact**: The primary deliverable (video generation) is absent. The existing artifacts suggest a different experiment (quantization benchmarking) was run instead of the specified "Long Video Generation" infrastructure validation.

**3. Documentation and Contract Absence**
The `plan.md` requires `contracts/inference_output.schema.yaml` and `contracts/metrics_report.schema.yaml` to define validation schemas.
- **Defect**: No `contracts/` directory exists. No `docs/reproducibility/` directory exists (as noted in the data summary).
- **Impact**: Without these schema definitions, the project cannot programmatically validate that the output conforms to the research requirements, violating the reproducibility principle.

**4. File Naming and Location Mismatch**
- **Defect**: The entry point `longlive_quant_benchmark.py` is at the root, whereas the plan specifies `src/inference/inference.py` as the primary entry point.
- **Impact**: The execution path does not match the documented plan, breaking the traceability between the spec and the code.

## Required Changes

- **Reorganize the entire project structure** to match `plan.md`: Create `src/`, `src/configs/`, `src/inference/`, `src/scripts/`, `src/tests/`, `contracts/`, `results/`, and `outputs/` directories. Move `requirements.txt` to the root (if not already) and ensure all source code is inside `src/`.
- **Implement the missing `inference.py` and `inference_sp.py` scripts** inside `src/inference/` as defined in `tasks.md` (T019, T022) to handle video generation, replacing the current `longlive_quant_benchmark.py` which does not fulfill the spec's video generation requirement.
- **Create the required contract schemas** (`contracts/inference_output.schema.yaml` and `contracts/metrics_report.schema.yaml`) as defined in `tasks.md` (T006, T007) to enable automated validation of outputs.
- **Generate the required artifacts**: Execute the corrected pipeline to produce a valid video file in `outputs/` and a `results/metrics.json` file conforming to the new schema, replacing the current benchmark CSV/JSON which do not meet the spec's success criteria (SC-002, SC-003).
- **Update `README.md` and `docs/reproducibility/`** to reflect the new directory structure and provide accurate instructions for running the `src/inference/inference.py` script on a CPU-only runner.
