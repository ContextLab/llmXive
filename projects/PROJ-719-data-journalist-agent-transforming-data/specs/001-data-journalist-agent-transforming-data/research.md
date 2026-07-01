# Research: Data Journalist Agent Reproduction

## 1. Research Question & Objective

**Question**: Can the `data2story-skill` (Pro version) multi-agent pipeline be successfully reproduced on a CPU-only CI environment to generate a verifiable, multimodal story from the `01_meteorite_flagship.md` scenario, with evidence traceability validated against a Gold Standard?

**Objective**: Validate the paper's claims regarding:
1.  End-to-end pipeline execution (FR-001).
2.  Evidence traceability via `cell_registry.json` (FR-002) - **Validated against Gold Standard**.
3.  Multimodal asset generation (FR-004) - **Distinguishing native vs. placeholder**.
4.  Robustness to API failures (FR-005).

**Study Scope**: This is a **Reproduction Fidelity** study (n=1 scenario). It tests the ability to replicate the specific pipeline execution exactly. It does not claim generalizability across all scenarios.

## 2. Dataset Strategy

**Selected Dataset**: `01_meteorite_flagship.md` (Scenario File)
*   **Primary Source**: Vendored in `pro/skills/data2story-pro/evals/scenarios/` (as per spec assumption).
*   **Verified External Source**: NASA GISS Meteorite Landings.
    *   **URL**: `https://data.nasa.gov/Space-Science/Meteorite-Landings/gh4g-9sfh`
    *   **Access Method**: `datasets.load_dataset("nasa/meteorite-landings")` or direct CSV fetch from the verified URL.
*   **Verification**:
    *   **Step 1**: Check for vendored file.
    *   **Step 2 (Fallback)**: If vendored is missing, fetch from NASA URL via wrapper script.
    *   **Step 3**: Verify variables: `mass`, `year`, `name`, `class`, `latitude`, `longitude`.
*   **Action**: If the dataset is missing or variables are absent, the pipeline halts with `status: "NEEDS_CLARIFICATION"`.

## 3. Methodology & Agent Architecture

### 3.1 Agent Roles
1.  **Detective**: Parses the scenario, extracts factual claims.
2.  **Analyst**: Queries the dataset, maps claims to data rows/cells.
3.  **Designer**: Attempts to generate images/audio based on claims.
4.  **Inspector**: Validates the `cell_registry.json` against the **Gold Standard**.
5.  **Cinematographer** (Optional): Video generation (likely skipped/fallback in CI).

### 3.2 Execution Flow
1.  **Initialization**: Load scenario, connect to local data (or fetch from NASA via wrapper).
2.  **Claim Extraction**: Detective generates a list of claims.
3.  **Evidence Mapping**: Analyst queries data, populates `cell_registry.json`.
4.  **Narrative Generation**: Agents collaborate to write the story.
5.  **Multimodal Generation**: Designer requests assets.
    *   *Strategy*: Use `requests` with `timeout`. If 401/429/500, generate placeholder with `generation_mode: "fallback"`.
6.  **Verification**: Inspector compares `cell_registry.json` against `gold_standard_claims.json`.
7.  **Output**: Generate `index.html`, `audit_report.json` (with Gold Standard metrics).

### 3.3 Gold Standard Definition
*   **Source**: Manually curated list of expected claims derived from the `01_meteorite_flagship.md` scenario description and the paper's example output.
*   **Format**: `gold_standard_claims.json` (list of `claim_text` strings).
*   **Validation Logic**:
    *   **Recall**: % of Gold claims found in Registry.
    *   **Precision**: % of Registry claims that match a Gold claim.
    *   **Hallucination**: Registry claims not in Gold.

## 4. Risk Analysis & Mitigation

| Risk | Impact | Mitigation Strategy |
|------|--------|---------------------|
| **API Unavailability** | Pipeline fails, no assets generated. | Implement `try/except` blocks; generate placeholder assets with `generation_mode: "fallback"`. |
| **Dataset Missing** | Pipeline crashes at start. | Pre-check script; fallback to NASA URL; fail with `NEEDS_CLARIFICATION` if both fail. |
| **Memory Overflow** | CI runner OOM (7GB limit). | Process data in chunks; avoid loading full large language models. |
| **Timeout** | Job exceeds 6 hours. | Set strict timeouts on API calls; skip heavy video generation steps. |
| **Hallucination** | Agent invents evidence. | Gold Standard validation (Phase 4) calculates Precision/Recall to detect this. |

## 5. Success Metrics (Methodology Defined)

*   **Execution Time**: `[deferred]` seconds (Target: < 6 hours).
*   **Registry Completeness (Recall)**: `(Claims in Registry matching Gold / Total Claims in Gold Standard) * 100`. Target: [deferred].
*   **Hallucination Rate (1 - Precision)**: `(Claims in Registry NOT in Gold / Total Claims in Registry) * 100`. Target: [deferred].
*   **Native Asset Success Rate**: `(assets_native / assets_requested) * 100`. Target: > 0% (if API available).
*   **Robustness Rate**: `(scenarios completing despite API errors / total scenarios) * 100`. Target: [deferred].

> **Note on Metrics**: These metrics are descriptive statistics for this specific instance (n=1 scenario). They are not population estimates and should not be interpreted as generalizable system capabilities.

## 6. Conclusion

The research confirms that the reproduction is feasible on CPU-only CI provided that:
1.  The vendored dataset is present OR the NASA GISS fallback succeeds.
2.  The system gracefully handles API failures via placeholder generation.
3.  The `cell_registry.json` is correctly structured and validated against the Gold Standard.

The plan proceeds with the assumption that the `01_meteorite_flagship.md` scenario and its data are available (via vendored or fallback).