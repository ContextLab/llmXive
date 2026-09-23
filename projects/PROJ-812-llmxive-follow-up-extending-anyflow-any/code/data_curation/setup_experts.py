"""
setup_experts.py

Generates the expert roster (data/raw/experts.json) and the annotation rubric
(data/raw/rubric_definition.md) required for the human-in-the-loop verification
workflow.

This script satisfies:
- FR-014: Expert roster and adjudication protocol.
- FR-031: Explicit annotation guidelines (rubric).

It does NOT fetch external data; it generates the configuration artifacts
based on the project's predefined requirements for the llmXive pipeline.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import logging utilities from the existing project structure
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution if package structure isn't fully installed yet
    import logging
    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Constants for file paths relative to project root
DATA_RAW_DIR = Path("data/raw")
EXPERTS_FILE = DATA_RAW_DIR / "experts.json"
RUBRIC_FILE = DATA_RAW_DIR / "rubric_definition.md"

def generate_expert_roster() -> List[Dict[str, Any]]:
    """
    Generates a list of expert definitions.
    
    In a real production environment, this might fetch from a database or
    a pre-approved list of human annotators. For this pipeline, we define
    a standard set of expert roles required by the specification (FR-014)
    to ensure the adjudication workflow has the necessary actors.
    
    Returns:
        List of expert dictionaries with 'id', 'role', and 'specialization'.
    """
    experts = [
        {
            "id": "EXP-001",
            "role": "Primary Annotator",
            "specialization": "Video Continuity & Motion Analysis",
            "status": "active",
            "adjudication_authority": False
        },
        {
            "id": "EXP-002",
            "role": "Primary Annotator",
            "specialization": "Video Continuity & Motion Analysis",
            "status": "active",
            "adjudication_authority": False
        },
        {
            "id": "EXP-003",
            "role": "Primary Annotator",
            "specialization": "Video Continuity & Motion Analysis",
            "status": "active",
            "adjudication_authority": False
        },
        {
            "id": "EXP-004",
            "role": "Adjudicator",
            "specialization": "Senior Video Forensics",
            "status": "active",
            "adjudication_authority": True
        },
        {
            "id": "EXP-005",
            "role": "Adjudicator",
            "specialization": "Senior Video Forensics",
            "status": "active",
            "adjudication_authority": True
        }
    ]
    return experts

def generate_rubric_definition() -> str:
    """
    Generates the content for the annotation rubric (guidelines).
    
    This document defines the scoring criteria for 'continuous' vs 'discontinuous'
    motion, ensuring blinding and consistency as required by FR-002 and FR-031.
    
    Returns:
        Markdown string containing the full rubric.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    rubric_content = f"""# Annotation Rubric: Video Continuity Verification

**Project**: llmXive Follow-up: Extending AnyFlow
**Version**: 1.0
**Generated**: {timestamp}

## 1. Objective
The goal of this annotation task is to determine the semantic continuity of video clips
based **solely** on visual pixel information. You are to assess whether the motion within
a clip is physically plausible and continuous, or if it contains a scene cut, jump, or
artificial discontinuity.

## 2. Blinding Protocol (CRITICAL)
- **NO METRICS**: You must NOT view any model outputs, divergence scores, or latent trajectories.
- **PIXEL ONLY**: Your judgment must be based exclusively on the rendered video frames.
- **ISOLATION**: Do not discuss specific clip contents with other annotators during the session.

## 3. Scoring Scale
You will provide a score between **0.0** and **1.0** for each clip.

| Score Range | Interpretation | Description |
| :--- | :--- | :--- |
| **0.0 - 0.3** | **Continuous** | Motion is smooth, physically plausible, and temporally coherent. No obvious cuts. |
| **0.4 - 0.6** | **Ambiguous** | Motion has minor artifacts or is difficult to judge; potential subtle cuts. |
| **0.7 - 1.0** | **Discontinuous** | Clear scene cut, jump cut, or impossible motion transition. Obvious discontinuity. |

## 4. Decision Criteria
### Indicators of Continuity (Low Score)
- Smooth camera pans or object movement.
- Consistent lighting and background across frames.
- Natural acceleration/deceleration patterns.

### Indicators of Discontinuity (High Score)
- Sudden change in background or lighting.
- "Jump" in object position or camera angle.
- Inconsistent motion vectors (e.g., object teleports).
- Abrupt audio-visual mismatch (if audio were visible, but focus on pixels).

## 5. Adjudication Process
- If two primary annotators (EXP-001 to EXP-003) differ by **> 0.4** (on the 0-1 scale),
  the case is automatically flagged for adjudication.
- An adjudicator (EXP-004 or EXP-005) will review the clip and provide a final binding score.
- The adjudicator's score overrides the primary scores in the final dataset.

## 6. Data Integrity
- Once a score is submitted, it is logged immutably.
- Do not attempt to reverse-engineer the model's behavior; focus on ground-truth visual evidence.

## 7. Expert Roster Reference
Refer to `data/raw/experts.json` for the list of active expert IDs and their roles.
"""
    return rubric_content

def main():
    """
    Main entry point to generate the experts.json and rubric_definition.md files.
    """
    logger.info("Starting setup_experts.py to generate configuration artifacts.")
    
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Generate and write experts.json
    logger.info(f"Generating expert roster: {EXPERTS_FILE}")
    experts = generate_expert_roster()
    
    with open(EXPERTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(experts, f, indent=2)
    
    logger.info(f"Successfully wrote {len(experts)} experts to {EXPERTS_FILE}")
    
    # 2. Generate and write rubric_definition.md
    logger.info(f"Generating annotation rubric: {RUBRIC_FILE}")
    rubric = generate_rubric_definition()
    
    with open(RUBRIC_FILE, 'w', encoding='utf-8') as f:
        f.write(rubric)
    
    logger.info(f"Successfully wrote rubric to {RUBRIC_FILE}")
    
    logger.info("setup_experts.py completed successfully.")

if __name__ == "__main__":
    main()