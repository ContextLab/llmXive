import os
import sys
from pathlib import Path
from typing import Optional

from config import get_project_root, get_ethics_dir, get_data_dir

PROJECT_ID = "PROJ-317-the-impact-of-visual-detail-on-false-mem"
IRB_DOC_NAME = "irb_approval_final.pdf"
IRB_DOC_PLACEHOLDER = "irb_placeholder.md"

def ensure_ethics_artifacts():
    """
    Generates ethics artifacts (informed_consent.md and irb_placeholder.md)
    based on the GDPR template and project specifics.

    VERIFICATION STEP:
    Checks for the existence of a real IRB approval document (or the placeholder
    if the real one is not yet available, but logs a critical warning).
    If the task is run in 'recruitment' mode (implied by the presence of a real IRB doc),
    it verifies the real doc exists. If not, it fails loudly as per requirements.
    """
    project_root = get_project_root()
    ethics_dir = get_ethics_dir()
    
    # Ensure directory exists
    ethics_dir.mkdir(parents=True, exist_ok=True)

    consent_path = ethics_dir / "informed_consent.md"
    irb_path = ethics_dir / "irb_placeholder.md"
    real_irb_path = ethics_dir / IRB_DOC_NAME

    # 1. Verify IRB Status
    # The requirement states: "Must include a verification step to ensure a real IRB 
    # approval document exists before recruitment begins; if no IRB doc is found, 
    # the task must fail."
    # We check for the real IRB document. If it doesn't exist, we check if the 
    # placeholder exists to allow generation of the text artifacts, but we raise 
    # a critical error if the user intends to recruit (simulated by a flag or 
    # strict check). For this implementation, we will fail if the real IRB doc 
    # is missing AND the placeholder is also missing (indicating a setup failure),
    # OR if the task is strictly enforcing the "must fail" clause when no IRB is present.
    
    has_real_irb = real_irb_path.exists()
    has_placeholder = irb_path.exists()

    if not has_real_irb:
        # If we are generating artifacts, we assume this is a setup phase.
        # However, the task says "if no IRB doc is found, the task must fail".
        # This implies the generation script should not proceed successfully 
        # without the IRB document being accounted for.
        # We will generate the placeholder text but raise an error to halt the pipeline
        # if the real IRB is missing, as per the strict constraint.
        raise FileNotFoundError(
            f"CRITICAL: No real IRB approval document found at {real_irb_path}. "
            f"Recruitment cannot begin. Please obtain IRB approval for {PROJECT_ID} "
            "and place the document in the ethics directory before proceeding."
        )

    # If we reach here, the real IRB exists. We proceed to generate/update the text artifacts.
    
    # Generate Informed Consent
    consent_content = generate_informed_consent_content()
    with open(consent_path, "w", encoding="utf-8") as f:
        f.write(consent_content)
    
    # Generate IRB Placeholder (updated with project ID)
    # Even if real IRB exists, we ensure the placeholder text is updated with the project ID
    # for the record, though the real file is the source of truth.
    irb_content = generate_irb_placeholder_content()
    with open(irb_path, "w", encoding="utf-8") as f:
        f.write(irb_content)

    print(f"Ethics artifacts generated successfully in {ethics_dir}")
    return True

def generate_informed_consent_content() -> str:
    project_root = get_project_root()
    template_path = project_root / "docs" / "ethics" / "gdpr_consent_template.md"
    
    # Fallback to a generated string if template is missing, but prefer reading template
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        # Base template content if file is missing (should not happen in real setup)
        template = """
# Informed Consent Form

## Study Title: The Impact of Visual Detail on False Memory Susceptibility ({{project_id}})

## Principal Investigator
[Researcher Name]
[Institution]
[Contact Information]

## Introduction
You are invited to participate in a research study investigating how visual detail in images affects the formation of false memories. This document explains the purpose, procedures, risks, and benefits of the study. Please read it carefully and ask questions if anything is unclear.

## Purpose of the Study
The goal of this research is to understand how the level of visual detail in stimuli influences susceptibility to false memories. This study contributes to the broader understanding of memory construction and distortion.

## Procedures
If you agree to participate, you will be asked to:
1. View a series of images with varying levels of visual detail.
2. Complete a brief distractor task (arithmetic questions).
3. Answer recognition questions about the images, including both true and false details.
4. Provide demographic information (optional).

The entire session will take approximately 15-20 minutes.

## Potential Risks
The risks associated with this study are minimal. You may experience mild fatigue from the visual tasks. If you feel uncomfortable at any point, you may pause or withdraw from the study without penalty.

## Potential Benefits
While there are no direct benefits to you, your participation will help advance scientific understanding of memory processes.

## Voluntary Participation
Your participation is entirely voluntary. You may choose not to participate or withdraw at any time without any negative consequences.

## Data Confidentiality and Usage
All data collected will be anonymized. Your responses will be stored securely and accessed only by the research team. No personally identifiable information (PII) will be published or shared.
**Data Usage**: Data will be used solely for the purpose of this research study and potentially for future academic publications related to memory science, in compliance with GDPR Art. 6 & 7.

## Right to Withdraw
You have the **Right to Withdraw** at any time without giving a reason. If you withdraw, your data will be deleted immediately unless it has already been anonymized and aggregated, in which case it cannot be removed.

## GDPR-Compliant Anonymization Workflow
In accordance with **GDPR Art. 6 & 7**, this study adheres to the following anonymization workflow:
1. **Pseudonymization**: Direct identifiers are replaced with a unique code immediately upon collection.
2. **Separation**: The key linking codes to identities is stored separately from the research data.
3. **Deletion**: Upon study completion or participant request, all re-identifiable data is securely deleted.
4. **Contact Info**: For questions regarding your rights or data, contact the Data Protection Officer at [DPO Email] or the PI at [PI Email].

## Contact Information
If you have questions about the study, please contact:
- [Researcher Name]: [Email]
- [Institutional Review Board]: [Email/Phone]

## Consent Statement
By proceeding, you confirm that:
- You have read and understood this consent form.
- You are at least 18 years of age.
- You voluntarily agree to participate in this study.

[ ] I consent to participate in this study.

---
*This template is compliant with GDPR requirements for data protection and informed consent.*
"""

    # Inject Project ID
    content = template.replace("{{project_id}}", PROJECT_ID)
    
    # Ensure mandatory clauses are present (simple check)
    mandatory_phrases = [
        "Data Usage",
        "Right to Withdraw",
        "Contact Info",
        "GDPR Art. 6",
        "GDPR Art. 7"
    ]
    
    for phrase in mandatory_phrases:
        if phrase not in content:
            # If missing, append to the end of the relevant section or warn
            # For this implementation, we assume the template is correct or we fix it programmatically
            if "Data Usage" not in content:
                content += "\n\n## Data Usage\nData will be used strictly for research purposes."
            if "Right to Withdraw" not in content:
                content += "\n\n## Right to Withdraw\nYou may withdraw at any time."
            if "Contact Info" not in content:
                content += "\n\n## Contact Info\nContact us at email@example.com."
            if "GDPR Art. 6" not in content:
                content += "\n\n*Compliance: GDPR Art. 6 & 7*"

    return content

def generate_irb_placeholder_content() -> str:
    content = f"""# IRB Approval Placeholder

## Study Protocol Summary
**Title**: The Impact of Visual Detail on False Memory Susceptibility
**Project ID**: {PROJECT_ID}
**Protocol ID**: [To be assigned by IRB]
**Principal Investigator**: [Researcher Name]
**Institution**: [Institution Name]

## Study Overview
This study investigates how visual detail in stimuli affects false memory formation. Participants will view manipulated images (enhanced or reduced detail), complete a distractor task, and answer recognition questions.

## Participant Recruitment
Participants will be recruited via [method, e.g., university participant pool, online platforms]. Inclusion criteria: adults (18+), normal or corrected-to-normal vision. Exclusion criteria: history of neurological disorders affecting memory.

## Data Management
- All data will be anonymized using unique participant IDs.
- No personally identifiable information (PII) will be stored with response data.
- Data will be stored on secure, password-protected servers.
- Access is restricted to the core research team.

## Risk Mitigation
- Minimal risk: Participants may experience mild fatigue.
- Right to withdraw at any time without penalty.
- Debriefing provided after the study to explain the purpose and address any concerns.

## Ethical Considerations
- Informed consent will be obtained from all participants.
- Confidentiality will be maintained in accordance with GDPR and institutional policies.
- The study has been designed to minimize any potential psychological discomfort.

## IRB Approval
This document serves as a placeholder for the official IRB approval letter. The actual approval must be obtained before any data collection begins.

**IRB Approval Number**: [To be assigned]
**Approval Date**: [To be assigned]
**Expiration Date**: [To be assigned]

---
*This placeholder must be replaced with the official IRB approval documentation prior to study initiation.*
"""
    return content

def main():
    try:
        ensure_ethics_artifacts()
        print("SUCCESS: Ethics artifacts generated and verified.")
        return 0
    except FileNotFoundError as e:
        print(f"FAILURE: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during ethics artifact generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())