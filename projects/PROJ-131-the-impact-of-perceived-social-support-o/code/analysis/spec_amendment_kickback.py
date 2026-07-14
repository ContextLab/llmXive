"""
Kickback Task T041: Spec Amendment Proposal Generator

This script generates a formal Pull Request description and a
methodological justification document to amend the project specification.
It addresses the conflict between the original dual-dataset synthetic cohort
requirement and the practical feasibility of the single-dataset approach.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Ensure we can import from the project root if run as a script
# but this module lives in code/analysis, so we adjust sys.path if necessary
# for standalone execution during the kickback process.
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from logger import get_logger

logger = get_logger(__name__)

PR_TITLE = "feat(spec): Amend specification to adopt single-dataset approach or clarify dual-dataset fallback"

PR_BODY_TEMPLATE = """
## Summary
This PR proposes an amendment to `specs/001-social-support-resilience/spec.md` to resolve a critical methodological constraint identified during implementation (Task T041).

The original specification requires a **dual-dataset synthetic cohort** (GSS 2022 + Cyberbullying Survey 2021) to perform propensity score matching for harmonization. However, implementation analysis reveals that the GSS 2022 dataset **lacks the specific psychometric items** (e.g., PCL-5, specific harassment severity scales) required for the study's core outcomes.

## The Problem
1.  **Data Incompatibility**: GSS 2022 does not contain the necessary PCL-5 or detailed harassment exposure variables required to compute the target outcomes (Depression, Anxiety, PTSD) as defined in `specs/001-social-support-resilience/data-model.md`.
2.  **Fallback Mechanism**: The current pipeline (T018) is designed to skip GSS ingestion if critical variables are missing, effectively proceeding with a **single-dataset** (Cyberbullying Survey 2021) approach.
3.  **Methodological Shift**: Proceeding with a single dataset changes the statistical approach from **Propensity Score Matching (PSM)** to **Inverse Probability Weighting (IPW)** or standard regression adjustment, as there is no second "treatment" group (GSS) to match against.

## Proposed Amendments
Please review and select **one** of the following options for the spec update:

### Option A: Retain Dual-Dataset Requirement (Strict)
*   **Action**: Update spec to explicitly state that the study is contingent on finding a GSS year with matching PCL-5 items (e.g., GSS 2021 or 2023 if available) OR a different public dataset.
*   **Implication**: If no suitable second dataset is found, the study scope must be reduced or cancelled.
*   **Revised FR-001**: "The system shall ingest two distinct datasets (GSS + Cyberbullying) containing overlapping psychometric variables."

### Option B: Formalize Single-Dataset Approach (Recommended)
*   **Action**: Update spec to adopt the single-dataset approach (Cyberbullying Survey 2021) as the primary cohort, using IPW for internal covariate balance rather than external harmonization.
*   **Justification**: The Cyberbullying Survey 2021 contains the full suite of required variables (CES-D, GAD-7, PCL-5, Social Support, Harassment).
*   **Revised FR-001**: "The system shall construct a synthetic cohort from the Cyberbullying Survey 2021 using Inverse Probability Weighting to adjust for selection bias."
*   **Revised SC-001**: "Standardized Mean Differences (SMD) for covariates within the weighted single-dataset cohort must be ≤ 0.1."

## Methodological Justification
The single-dataset approach is statistically valid for this research question if the goal is to estimate the effect of social support on resilience *within* the population of online harassment victims. The "synthetic" aspect shifts from **cross-dataset harmonization** to **internal re-weighting** to simulate a balanced population. This avoids the "garbage-in-garbage-out" risk of forcing a match between GSS (no PCL-5) and Cyberbullying (has PCL-5).

## Request for Review
@spec-owner: Please confirm which option (A or B) aligns with the research goals.
- If **Option A**: We need to identify a valid second dataset immediately.
- If **Option B**: We will update the spec to reflect the single-dataset IPW methodology and adjust the pipeline accordingly.

"""

METHOD_LOGIC_TEMPLATE = """
# Methodological Justification: Single-Dataset vs. Dual-Dataset Cohort

## 1. Context
The study investigates the impact of perceived social support on resilience to online harassment.
Original Plan: Harmonize GSS 2022 and Cyberbullying Survey 2021 via Propensity Score Matching.

## 2. Data Audit Findings
During the ingestion phase (Task T012/T018), the following was observed:
- **Cyberbullying Survey 2021**: Contains CES-D, GAD-7, PCL-5, Social Support, and Harassment Severity.
- **GSS 2022**: Contains demographic variables (Age, Gender, Education, Income) and general mental health proxies, but **lacks** PCL-5 (PTSD) and specific online harassment severity scales.

## 3. Implication of Missing Data
Propensity Score Matching (PSM) requires a common support region where covariates overlap between two groups.
- If Group 1 (GSS) lacks the outcome variables (PCL-5, Harassment), we cannot define the "treatment" or "outcome" space for matching.
- Attempting to match on demographics alone and then imputing missing outcomes is methodologically unsound and introduces massive bias.

## 4. Proposed Solution: Single-Dataset IPW
Instead of external harmonization, we propose using the **Cyberbullying Survey 2021** as the sole source.
- **Technique**: Inverse Probability Weighting (IPW) based on the probability of being in a "high social support" vs "low social support" group, or weighting by the inverse of the propensity to be in the observed sample relative to a target population (if external benchmarks exist).
- **Alternative**: If no external benchmark exists, we treat the dataset as a representative sample of the "online harassment victim" population and use standard regression with robust standard errors, ensuring covariate balance via weighting within the sample.

## 5. Conclusion
The dual-dataset approach is not feasible without a different second dataset. The single-dataset approach is scientifically valid for estimating associations within the specific population of interest (online harassment victims), provided the weighting strategy is clearly defined.

"""

def generate_kickback_artifacts(output_dir: Optional[Path] = None) -> None:
    """
    Generates the PR description and methodological justification files.
    """
    if output_dir is None:
        output_dir = project_root / "specs" / "001-social-support-resilience"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate PR Body
    pr_file = output_dir / "PR_T041_AMENDMENT_PROPOSAL.md"
    with open(pr_file, "w", encoding="utf-8") as f:
        f.write(PR_BODY_TEMPLATE)
    
    logger.info(f"Generated PR description at: {pr_file}")

    # 2. Generate Methodological Justification
    method_file = output_dir / "METHODOLOGICAL_JUSTIFICATION_T041.md"
    with open(method_file, "w", encoding="utf-8") as f:
        f.write(METHOD_LOGIC_TEMPLATE)
    
    logger.info(f"Generated methodological justification at: {method_file}")

    # 3. Generate a summary file for the spec owner
    summary_file = output_dir / "T041_ACTION_REQUIRED.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"""
ACTION REQUIRED: Spec Amendment (Task T041)

The pipeline has identified a critical data gap preventing the dual-dataset approach.
Please review the generated files:
1. {pr_file.name} - The formal PR description for the spec update.
2. {method_file.name} - The detailed methodological justification.

Decision Needed:
- Option A: Find a new second dataset (e.g., GSS 2021/2023 if PCL-5 exists).
- Option B: Update spec to adopt the Single-Dataset (Cyberbullying 2021) approach with IPW.

Until this decision is made, the pipeline will proceed with the single-dataset fallback logic.
""")
    
    logger.info(f"Generated action summary at: {summary_file}")

def main() -> None:
    """
    Entry point for the kickback task.
    """
    logger.info("Starting T041: Spec Amendment Kickback Generation")
    generate_kickback_artifacts()
    logger.info("T041 Kickback artifacts generated successfully.")

if __name__ == "__main__":
    main()