# Quickstart Guide: Evaluating the Impact of LLM-Generated Code Documentation

This guide outlines the steps to execute the research pipeline for project PROJ-274.
Ensure all dependencies are installed (`pip install -r requirements.txt`) before running.

## Phase 0: Research & Methodology Validation

1. **Generate Research Protocol**:
 (Task T070 - Manual/Scripted generation of `specs/001-evaluating-the-impact-of-llm-generated-c/research.md`)
 *Ensure the document explicitly states that the 'decision tree' is removed and Welch's ANOVA is pre-specified.*

2. **Validate Methodology (T070c)**:
 Run the methodology validator to ensure `research.md` adheres to the Critical Methodological Shift.
 ```bash
 python code/validation/methodology_validator.py
 ```
 *Success creates `state/methodology_valid.lock`. Failure aborts the pipeline.*

## Phase 1: Setup & Recruitment

3. **Initialize Project Structure (T001a)**:
 ```bash
 python code/setup_project.py
 ```

4. **Initialize Run Metadata (T010b)**:
 ```bash
 python code/utils/run_metadata.py
 ```

5. **Initialize Recruitment Tracker (T073b)**:
 ```bash
 python code/recruitment/tracker.py
 ```

6. **Assign Participants (T014)**:
 Run in Real Mode (for pilot) or Mock Mode (for testing).
 ```bash
 # Real Mode (requires pre-existing participant records in data/raw/participants_raw.json)
 python code/experiment/assignment.py --mode real

 # Mock Mode (generates synthetic assignment for testing)
 python code/experiment/assignment.py --mode mock --participants 5
 ```

## Phase 2: Repository Selection

7. **Generate Candidate Repos List (T020a)**:
 ```bash
 python code/run_repo_fetch.py --init-candidates
 ```

8. **Pin Repository Commits (T021c-0)**:
 ```bash
 python code/run_repo_fetch.py --pin-commits
 ```

9. **Calculate Metrics & Rubric (T021a, T021b, T021c)**:
 ```bash
 python code/run_metrics_collection.py
 python code/run_doc_quality_rubric.py
 ```

10. **Filter & Select Repos (T021d-2, T021d-3)**:
 ```bash
 python code/run_rubric_and_metrics.py
 ```

11. **Generate Covariates (T021e)**:
 ```bash
 python code/run_covariate_collection.py
 ```

12. **Repository Selection Gate (T021f)**:
 ```bash
 python code/run_repo_selection_gate.py
 ```

## Phase 4: Documentation Generation (US2)

13. **Generate Documentation (T076)**:
 ```bash
 python code/generation/doc_pipeline.py --input data/raw/repo_selection_rubric.json
 ```

## Phase 3: Experiment Execution (US1)

14. **Run Experiment (T075b)**:
 ```bash
 # Mock Experiment
 python code/experiment/experiment.py --mode mock --participants 3

 # Real Experiment (requires real participants)
 python code/experiment/experiment.py --mode real
 ```

## Phase 5: Data Cleaning

15. **Run Cleaning Pipeline (T032)**:
 ```bash
 python code/run_cleaning_pipeline.py
 ```

## Phase 6: Statistical Analysis (US3)

16. **Run Analysis (T036b)**:
 ```bash
 python code/analysis/stats_runner.py --input data/processed/cleaned_dataset.csv --output data/reports/primary_analysis_results.json
 ```

## Final Report

17. **Generate Final Report (T041)**:
 ```bash
 python code/analysis/prepare_research_protocol.py
 ```