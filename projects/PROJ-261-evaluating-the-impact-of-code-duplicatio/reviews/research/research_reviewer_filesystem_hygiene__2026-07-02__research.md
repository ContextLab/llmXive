---
action_items:
- id: e81cfa403a45
  severity: writing
  text: 'Create/Move Raw Data Artifact: Ensure projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw/github-code-sample.csv
    exists and is populated with the streamed dataset as per T018.'
- id: ef22c507462f
  severity: writing
  text: 'Generate Missing Processed Artifacts: Run the pipeline to generate data/processed/clone_metrics.csv,
    data/processed/perplexity_scores.csv, and data/processed/bug_detection_results.csv
    as mandated by T021, T020, and T031.'
- id: c856e8720f34
  severity: writing
  text: 'Generate Analysis Artifacts: Execute T034 and T042 to produce data/analysis/correlation_results.csv
    and populate data/analysis/figures/ with the required PNG/PDF plots.'
- id: b833a7d09615
  severity: writing
  text: 'Update Documentation Location and Content: Move docs/reproducibility/hyperparameters.md
    to specs/001-evaluate-code-duplication-llm-understanding/hyperparameters.md (or
    update plan.md to reflect the new location) and expand the content to explicitly
    list clone-detection thresholds (0.7, 0.8, 0.9) and random seeds.'
- id: 5188f004d3eb
  severity: writing
  text: 'Align Code Structure: Consolidate utils/checksum_visualizations.py and visualization/plotting.py
    into the single code/visualization.py module defined in plan.md, or update plan.md
    and all task references to reflect the new directory structure.'
artifact_hash: 4dd305993273af116dc6162814129dd77fcb7c0ed6b08fe4e79518710d2d79a2
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-07-02T07:21:00.441754Z'
reviewer_kind: llm
reviewer_name: research_reviewer_filesystem_hygiene
score: 0.0
verdict: minor_revision
---

The project exhibits significant filesystem hygiene violations that compromise reproducibility and violate Constitution Principle V (Versioning Discipline) and Principle III (Data Hygiene). While the directory structure is logically sound, the actual file placement, naming consistency, and documentation currency are defective.

**1. Inconsistent Artifact Paths (Plan vs. Reality)**
The `plan.md` explicitly defines the output structure under `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/` with subdirectories `raw/`, `processed/`, and `analysis/`. However, the `data summary` shows artifacts located at the root of the data directory or in undefined locations:
- `data/parse_failures.csv` exists, but `plan.md` implies it should be in `data/` (acceptable), yet `data/raw/github-code-sample.csv` is missing from the listing entirely.
- `data/analysis/bug_detection_summary.json` exists, but `plan.md` specifies `data/analysis/correlation_results.csv` and `data/analysis/figures/`. The presence of a `.json` summary instead of the mandated `.csv` correlation results indicates a deviation from the spec's data model.
- `data/quickstart_validation_results.json` is present, but `plan.md` does not define this artifact path.

**2. Missing Mandatory Artifacts**
Per `spec.md` (FR-008, FR-010) and `plan.md`, the following files are required but absent from the `data summary`:
- `data/raw/github-code-sample.csv`: The primary raw data artifact.
- `data/processed/clone_metrics.csv`: Explicitly listed in `plan.md` and `tasks.md` (T021), yet missing from the summary.
- `data/processed/perplexity_scores.csv`: Required by T020, missing.
- `data/processed/bug_detection_results.csv`: Required by T031, missing.
- `data/analysis/correlation_results.csv`: Required by T034, missing.
- `data/analysis/figures/`: The directory is missing entirely, despite T042 requiring plot generation.

**3. Documentation Currency and Location**
The `docs/reproducibility/hyperparameters.md` file (738 bytes) is incomplete. It lists the model but fails to document the specific clone-detection thresholds (0.7, 0.8, 0.9) and random seeds required by `spec.md` (SC-005) and `tasks.md` (T043). Furthermore, `plan.md` specifies that reproducibility documentation should reside in `specs/001-evaluate-code-duplication-llm-understanding/`, yet the file is located in `docs/reproducibility/`. This violates the "Single Source of Truth" principle regarding where documentation artifacts live.

**4. Code File Naming and Location**
The `code summary` lists `utils/checksum_visualizations.py` and `visualization/plotting.py`. The `plan.md` structure defines `code/visualization.py` as a single module. The split into `utils/` and `visualization/` subdirectories without corresponding updates to `plan.md` or `tasks.md` creates ambiguity about the canonical location of the visualization logic.

## Required Changes

- **Create/Move Raw Data Artifact**: Ensure `projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw/github-code-sample.csv` exists and is populated with the streamed dataset as per T018.
- **Generate Missing Processed Artifacts**: Run the pipeline to generate `data/processed/clone_metrics.csv`, `data/processed/perplexity_scores.csv`, and `data/processed/bug_detection_results.csv` as mandated by T021, T020, and T031.
- **Generate Analysis Artifacts**: Execute T034 and T042 to produce `data/analysis/correlation_results.csv` and populate `data/analysis/figures/` with the required PNG/PDF plots.
- **Update Documentation Location and Content**: Move `docs/reproducibility/hyperparameters.md` to `specs/001-evaluate-code-duplication-llm-understanding/hyperparameters.md` (or update `plan.md` to reflect the new location) and expand the content to explicitly list clone-detection thresholds (0.7, 0.8, 0.9) and random seeds.
- **Align Code Structure**: Consolidate `utils/checksum_visualizations.py` and `visualization/plotting.py` into the single `code/visualization.py` module defined in `plan.md`, or update `plan.md` and all task references to reflect the new directory structure.
