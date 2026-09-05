# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Status**: **BLOCKED** - Project is terminated for this revision due to missing verified data source.
**Deliverable**: Feasibility Report (JSON and Markdown) documenting the termination.

**Tests**: Unit tests for feasibility check logic and schema validation.

**Organization**: Tasks are grouped by the Feasibility Verification workflow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

---

## Phase 1: Feasibility Verification (Blocked State)

**Purpose**: Execute the feasibility check, confirm data unavailability, and generate the Feasibility Report as the sole deliverable.

**CRITICAL**: The plan states the project is **TERMINATED**. No statistical analysis, data ingestion, or visualization will be performed. The only valid output is the Feasibility Report.

### Gate: Feasibility Check

- [X] T001a [US1] **Implement Feasibility Check Script**: Create `src/feasibility.py`. This script reads `plan.md`, checks the `# Verified datasets` block for an American Gut Project URL, and exits with code 0 if found, code 1 if not.
  - **Action**: Implement logic to parse `plan.md` and validate the `# Verified datasets` block.
  - **Verification**: Assert `src/feasibility.py` exists and contains logic to check for the AGP URL. **[FR-001]**

- [X] T001b [US1] **Run Feasibility Check**: Execute `python src/feasibility.py`.
  - **Action**: Run the script.
  - **Expected Result**: Exit code 1 (Blocked).
  - **Deliverable**: `data/processed/data_feasibility_status.json` with keys: `status` ("blocked"), `reason` ("No verified data source found"), `timestamp`.
  - **Verification**: Assert exit code is 1 and `data/processed/data_feasibility_status.json` exists with correct content. **[FR-001] [FR-002]**

### Feasibility Report Generation

- [X] T002 [US1] **Generate Feasibility Report (JSON)**: Create `data/processed/feasibility_report.json`.
  - **Action**: Generate a JSON file with the following schema:
    ```json
    {
      "status": "blocked",
      "reason": "No verified data source found in plan.md",
      "timestamp": "<ISO8601>",
      "diversity_computation_status": "blocked",
      "correlation_analysis_status": "blocked",
      "visualization_status": "blocked",
      "exclusion_rates_status": "unmeasurable",
      "correlation_metrics_status": "unmeasurable"
    }
    ```
  - **Verification**: Assert file exists and contains all keys with correct values. **[FR-001] [FR-002] [FR-003] [FR-004] [FR-005] [FR-006] [SC-001] [SC-002] [SC-003]**

- [X] T003 [US1] **Document Data Unavailability**: Update `research.md` with a section documenting the absence of a verified AGP URL.
  - **Action**: Add a section "Data Unavailability" explaining the termination.
  - **Verification**: Assert `research.md` contains the section. **[FR-001]**

- [X] T004 [US1] **Document Feasibility Report Generation**: Update `quickstart.md` with a section documenting the Feasibility Report generation process.
  - **Action**: Add a section "Feasibility Report Generation" explaining how to run `src/feasibility.py`.
  - **Verification**: Assert `quickstart.md` contains the section. **[FR-001]**

- [X] T005 [US1] **Define Feasibility Report Schema**: Create `contracts/feasibility_report.schema.yaml`.
  - **Action**: Define the YAML schema for `data/processed/feasibility_report.json`.
  - **Verification**: Assert file exists and is valid YAML. **[FR-001]**

- [X] T006 [US1] **Generate Final Human-Readable Report**: Create `outputs/reports/feasibility_report.md`.
  - **Action**: Compile the JSON report into a Markdown summary.
  - **Verification**: Assert file exists and contains "Blocked" and "reason". **[FR-006]**

- [X] T007 [US1] **Verify Blocked Artifact Structure**: Verify the structure of `data/processed/feasibility_report.json` and `outputs/reports/feasibility_report.md`.
  - **Action**: Assert the JSON contains required keys and the Markdown contains required sections.
  - **Verification**: Assert structure matches expected schema. **[SC-005]**

- [X] T008 [US1] **Finalize Feasibility Report**: Ensure all blocked status reports are compiled into `outputs/reports/feasibility_report.md`.
  - **Action**: Verify the final report contains a summary of all blocked tasks.
  - **Verification**: Assert `outputs/reports/feasibility_report.md` exists and contains the summary. **[FR-006]**

---

## Future Work (Conditional on Data Availability)

*If a verified AGP URL is found in a future revision, the following tasks will be enabled:*

- **T013** — Download AGP data [FR-001]
- **T014** — Filter samples [FR-002]
- **T020a** — Compute alpha-diversity [FR-003]
- **T021** — Perform Spearman correlation [FR-004]
- **T022** — Apply BH correction [FR-005]
- **T027** — Generate visualizations [FR-006]
- **T035** — Verify reproducibility [SC-005]
- **T045** — Implement exponential backoff [FR-001]
- **T049** — Implement real dataset streaming [FR-001]
- **T050** — Implement strict data loader failure [FR-001]
- **T052** — Implement explicit "Fail Loud" check [FR-001]
- **T053** — Add unit test for "Fail Loud" behavior [FR-001]
- **T054** — Implement streaming logic documentation [FR-001]
- **T055** — Add integration test for correlation pipeline [FR-004]
- **T056** — Add integration test for placeholder plot generation [FR-006]
- **T057** — Implement Resource Usage Monitoring [SC-004]

---

## Dependencies & Execution Order

### Phase Dependencies

- **Feasibility Verification (Phase 1)**: No dependencies - can start immediately.
- **Future Work**: All depend on a verified AGP URL being found.

### Execution Order

1. **T001a**: Implement `src/feasibility.py`.
2. **T001b**: Run `src/feasibility.py`. (Exits 1).
3. **T002**: Generate `data/processed/feasibility_report.json`.
4. **T003**: Update `research.md`.
5. **T004**: Update `quickstart.md`.
6. **T005**: Create `contracts/feasibility_report.schema.yaml`.
7. **T006**: Generate `outputs/reports/feasibility_report.md`.
8. **T007**: Verify artifact structure.
9. **T008**: Finalize report.

---

## Notes

- **CRITICAL**: This revision is **TERMINATED**. No data processing is performed.
- **CRITICAL**: The only deliverable is the Feasibility Report.
- **CRITICAL**: All "Happy Path" tasks are moved to "Future Work" and are not executable.
- **CRITICAL**: Do not fabricate data. If the verified dataset is missing, the pipeline halts and generates the Feasibility Report.
- **NOTE**: Mock data paths have been removed. Pipeline validation is performed via unit tests with hardcoded data.
- **NEW**: T001-T008 implement the Feasibility Verification workflow as defined in Plan T001-T012.
- **NEW**: T013-T057 moved to "Future Work" section.