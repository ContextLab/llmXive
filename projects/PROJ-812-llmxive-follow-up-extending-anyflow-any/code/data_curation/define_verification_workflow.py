"""
Task T008b: Define Verification Workflow for Human-in-the-Loop Validation.

This script generates the `data/raw/verification_workflow.md` document which
outlines the expert roster, blinding protocol, and adjudication process
required for the human verification pool (US1).

It satisfies FR-001 and FR-013.
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Import local utilities from the project structure
from utils.logging import get_logger

logger = get_logger(__name__)

def generate_workflow_document() -> str:
    """
    Constructs the Markdown content for the verification workflow.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"""# Verification Workflow Protocol: AnyFlow Video Continuity Analysis

**Generated:** {timestamp}
**Project:** PROJ-812-llmxive-follow-up-extending-anyflow-any
**Task:** T008b
**Status:** Active

## 1. Purpose and Scope

This document defines the standard operating procedure (SOP) for human experts to verify
video continuity in the context of the "AnyFlow: Any-Step Video Diffusion Model" study.
The primary goal is to establish a ground-truth dataset of "continuous" vs. "cut" clips
to validate the flow-map divergence metric without introducing bias from model outputs.

This workflow satisfies requirements FR-001 (Human-in-the-Loop) and FR-013 (Blinding Protocol).

## 2. Expert Roster

The verification pool consists of a curated list of domain experts. Access to the
annotation tool is restricted to individuals listed in the `data/raw/experts.json` file.

### Roster Management
- **Source of Truth:** `data/raw/experts.json`
- **Access Control:** Experts must authenticate using their assigned ID.
- **Training:** All experts must complete the calibration pilot (N=50) and achieve
  a Cohen's Kappa score of ≥ 0.81 (FR-010) before accessing the full pool.

### Roles
1. **Primary Annotator:** Assigns continuity scores (0.0–1.0).
2. **Secondary Annotator:** Independently re-annotates 20% of clips for reliability.
3. **Adjudicator:** Resolves conflicts where |Score_A - Score_B| > 0.1.

## 3. Blinding Protocol (FR-002, FR-013)

To ensure unbiased ground truth, the following strict blinding measures are enforced:

### 3.1 Visual Blinding
- The annotation interface (`code/data_curation/annotation_tool.py`) displays **ONLY**
  raw pixel frames from the video clip.
- **NO** model metrics, divergence scores, confidence intervals, or metadata regarding
  the generation method are visible to the annotator.
- **NO** audio is played (if applicable), ensuring analysis is based solely on visual
  continuity.

### 3.2 Data Obfuscation
- Video file paths are replaced with generated Video IDs (e.g., `vid_8f3a2c`) to prevent
  recognition of specific source datasets (Kinetics/UCF101) that might bias expectations.
- The original file path is stored in a separate, encrypted manifest accessible only
  to the pipeline orchestrator, not the annotation UI.

## 4. Annotation Procedure

### 4.1 Scoring Scale
Experts assign a continuous score `S` ∈ [0.0, 1.0]:
- **0.0:** Perfectly continuous motion (no cuts, smooth flow).
- **1.0:** Hard cut or discontinuous motion (abrupt scene change).
- **Intermediate:** Gradual transitions or ambiguous cuts.

### 4.2 Workflow Steps
1. Load the next clip from the `data/raw/manually_verified_pool.csv`.
2. Review the pixel frames (blinded).
3. Input score `S` via the slider interface.
4. Submit. The system records:
   - `video_id`
   - `annotator_id`
   - `score`
   - `timestamp`
   - `sha256_checksum` of the frame sequence (for integrity).

## 5. Adjudication Process

If the discrepancy between two independent annotators exceeds the threshold (|S1 - S2| > 0.1):

1. **Trigger:** The system flags the clip for "Third-Party Review".
2. **Selection:** An adjudicator is randomly selected from the roster (excluding the original two).
3. **Resolution:** The adjudicator views the clip under the same blinding conditions.
4. **Final Score:** The adjudicator's score becomes the ground truth.
5. **Logging:** The decision is recorded in `data/raw/adjudication_log.csv`.

## 6. Data Integrity and Immutability

- **Write Protection:** Once a clip is annotated and the batch is finalized, the
  `data/raw/annotations.csv` file is set to read-only (chmod 444).
- **Checksum Locking:** A SHA-256 checksum file (`annotations.csv.sha256`) is generated
  immediately after the final write.
- **Verification:** Any downstream process (e.g., T012) must verify the checksum before
  proceeding.

## 7. Compliance and Audit

- All actions are logged with timestamps and user IDs.
- The `rubric_definition.md` (generated in T008c) serves as the reference guide for
  scoring criteria.
- Deviations from this protocol must be reported in the `data/raw/error_log.csv`.

---
*End of Verification Workflow Document*
"""
    return content

def main():
    """
    Main entry point to generate the verification workflow document.
    """
    logger.info("Starting T008b: Define Verification Workflow")

    # Define output path
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "verification_workflow.md"

    try:
        content = generate_workflow_document()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Successfully generated workflow document: {output_path}")

        # Verify the file exists and has content
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info("Verification workflow generation complete.")
        else:
            logger.error("Failed to generate content for workflow document.")
            raise RuntimeError("Output file is empty or missing.")

    except Exception as e:
        logger.error(f"Error generating verification workflow: {e}")
        raise

if __name__ == "__main__":
    main()