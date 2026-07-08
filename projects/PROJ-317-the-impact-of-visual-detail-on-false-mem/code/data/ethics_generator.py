import os
from pathlib import Path
from typing import Optional
from config import get_ethics_dir

def ensure_ethics_artifacts():
    """Create ethics artifacts if they don't exist."""
    ethics_dir = get_ethics_dir()
    ethics_dir.mkdir(parents=True, exist_ok=True)
    
    consent_path = ethics_dir / "informed_consent.md"
    irb_path = ethics_dir / "irb_placeholder.md"
    
    if not consent_path.exists():
        consent_content = """# Informed Consent Form

## Study Title: The Impact of Visual Detail on False Memory Susceptibility

### Purpose
This study investigates how visual detail influences false memory formation.

### Procedures
Participants will view images and answer recognition questions.

### Risks
Minimal risk. Participants may experience mild cognitive fatigue.

### Benefits
Contributes to understanding of memory formation.

### Confidentiality
All data is anonymized and stored securely.

### Contact
Researcher: [Name]
Email: [Email]
"""
        with open(consent_path, 'w') as f:
            f.write(consent_content)
    
    if not irb_path.exists():
        irb_content = """# IRB Approval Placeholder

## Protocol Number: [PENDING]

## Approval Date: [PENDING]

## Expiration Date: [PENDING]

## Notes
This document serves as a placeholder for IRB approval.
Actual approval must be obtained before data collection begins.
"""
        with open(irb_path, 'w') as f:
            f.write(irb_content)

def main():
    ensure_ethics_artifacts()
    print("Ethics artifacts ensured.")

if __name__ == "__main__":
    main()