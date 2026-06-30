"""
Script to generate ethics artifacts (Informed Consent and IRB Placeholder)
if they do not already exist. This ensures the data/ethics directory is populated
with the required templates for GDPR compliance and IRB submission.
"""
import os
from pathlib import Path
from typing import Optional

# Import config to ensure directories exist
try:
    from config import get_ethics_dir
except ImportError:
    # Fallback for standalone execution if config is not in path
    def get_ethics_dir() -> Path:
        return Path("data/ethics")

CONSENT_TEMPLATE = """# Informed Consent Form

**Study Title:** The Impact of Visual Detail on False Memory Susceptibility
**Principal Investigator:** [PI Name]
**Institution:** [Institution Name]
**Contact Information:** [Email] | [Phone]
**IRB Protocol Number:** [IRB-XXXX-XX] (Pending Approval)

---

## 1. Introduction
You are invited to participate in a research study investigating how visual detail in images influences the formation of false memories. This document explains the purpose, procedures, risks, and benefits of the study. Please read it carefully. Your participation is voluntary.

## 2. Purpose of the Study
The goal of this research is to understand the cognitive mechanisms underlying false memory formation. Specifically, we aim to determine whether images with higher levels of visual detail increase or decrease a participant's susceptibility to remembering details that were not actually present.

## 3. Procedures
If you agree to participate, you will be asked to:
1. **View Images:** You will be presented with a series of baseline images. Some images will be manipulated to have enhanced detail, while others will have reduced detail.
2. **Distractor Task:** Between image viewing sessions, you will complete a brief arithmetic distractor task to clear short-term memory.
3. **Recognition Task:** You will answer questions about the images, identifying whether specific details were present or absent. Some questions will refer to "lure" details that were never shown.
4. **Demographics:** You will provide basic demographic information (age, gender, education) for classification purposes.

The total time commitment is approximately 20–30 minutes.

## 4. Potential Risks and Discomforts
- **Psychological Discomfort:** You may experience mild frustration during the distractor task or confusion when answering recognition questions.
- **Privacy:** While we take extensive precautions, there is a minimal risk of data breach. All data will be anonymized and stored securely.
- **False Memory:** The study intentionally induces false memories for research purposes. You will be fully debriefed at the end of the session to clarify that some details you "remembered" were not real.

## 5. Potential Benefits
There are no direct benefits to you as a participant. However, the knowledge gained may contribute to a better understanding of human memory, with potential implications for eyewitness testimony and cognitive psychology.

## 6. Confidentiality and Data Protection (GDPR Compliance)
In accordance with the General Data Protection Regulation (GDPR):
- **Data Minimization:** We collect only the data strictly necessary for the research.
- **Anonymization:** Your name and contact information will not be stored with your experimental data. You will be assigned a unique Participant ID (e.g., P-001).
- **Right to Withdraw:** You may withdraw from the study at any time without penalty. If you withdraw before data processing, your data will be destroyed immediately.
- **Data Storage:** All data will be stored on encrypted, password-protected servers accessible only to the research team.
- **Right to Access/Rectify:** You have the right to request access to your personal data or request correction of inaccurate data.

## 7. Voluntary Participation
Your participation is entirely voluntary. You may refuse to participate or withdraw at any time without consequence.

## 8. Contact Information
If you have questions about the study, please contact:
- **Researcher:** [Name] at [Email]
- **Institutional Review Board (IRB):** [IRB Contact Info]

If you have questions about your rights as a research participant, please contact the IRB office.

## 9. Consent Statement
I have read (or had read to me) the information provided above. I understand the procedures, risks, and benefits described. I voluntarily agree to participate in this study.

________________________________________
**Participant Signature** | **Date**

________________________________________
**Researcher Signature** | **Date**

---
*Template Version: 1.0 | Last Updated: [Date]*
*Note: This document is a placeholder pending final IRB approval.*
"""

IRB_TEMPLATE = """# Institutional Review Board (IRB) Application Placeholder

**Project Title:** The Impact of Visual Detail on False Memory Susceptibility
**Protocol ID:** [PROJ-317-IRB-XXXX]
**Principal Investigator:** [PI Name]
**Department:** [Department Name]
**Institution:** [Institution Name]
**Submission Date:** [Date]

---

## 1. Study Summary
This study investigates the relationship between visual detail in stimuli and the susceptibility to false memory formation. Participants will view manipulated images (enhanced vs. reduced detail) and complete a recognition task involving true and false details.

## 2. Risk Category
**Category:** Minimal Risk
**Justification:** The study involves viewing images and answering questions. The induced false memories are temporary and will be fully debriefed. No sensitive personal data is collected beyond basic demographics.

## 3. Participant Recruitment
- **Target Population:** Adults (18+)
- **Recruitment Method:** [e.g., University participant pool, online advertising]
- **Inclusion Criteria:** Normal or corrected-to-normal vision, fluent in [Language].
- **Exclusion Criteria:** History of severe cognitive impairment or neurological disorders.

## 4. Data Management Plan
- **Data Collection:** Digital responses stored in CSV/JSON format.
- **Anonymization:** Direct identifiers (name, email) are stored separately from experimental data. Linking is done via a secure, encrypted key.
- **Retention:** Data will be retained for [X] years as per institutional policy, then securely destroyed.
- **Sharing:** De-identified data may be shared in public repositories (e.g., OSF) upon publication.

## 5. Informed Consent Process
- Consent will be obtained electronically prior to the start of the experiment.
- Participants must explicitly click "I Agree" after reading the consent form.
- A copy of the signed consent form will be emailed to the participant.

## 6. Deception and Debriefing
- **Deception:** The study involves the use of "lure" details that were never presented. Participants are not informed of this until the debriefing.
- **Debriefing:** Immediately following the session, participants will be shown the original images and informed about the true nature of the task. They will be provided with resources if they experience distress (though none is anticipated).

## 7. Privacy and GDPR Compliance
- **Lawful Basis:** Consent (Article 6(1)(a) GDPR).
- **Data Subject Rights:** Participants have the right to access, rectify, erase, and restrict processing of their data.
- **Data Protection Officer (DPO):** [DPO Contact Info]

## 8. Emergency Procedures
- In the unlikely event of participant distress, the session will be terminated immediately.
- Participants will be provided with contact information for counseling services if needed.

## 9. Approval Checklist
- [ ] Informed Consent Form attached (see `informed_consent.md`)
- [ ] Recruitment materials attached
- [ ] Data Management Plan attached
- [ ] Debriefing script attached
- [ ] Conflict of Interest disclosure submitted

---

### IRB Reviewer Comments / Action Items
*(To be completed by IRB)*

- [ ] **Exempt Review:** This study qualifies for exemption under [Category X].
- [ ] **Expedited Review:** Requires expedited review due to minimal risk.
- [ ] **Full Board Review:** Requires full board review.

**Decision:** [Approved / Pending / Rejected / Modifications Required]

**IRB Chair Signature:** ________________________ **Date:** __________

---
*This document is a placeholder for the official IRB submission and must be updated with final protocol numbers and approval dates.*
"""

def ensure_ethics_artifacts() -> None:
    """
    Generates the ethics artifacts (informed_consent.md and irb_placeholder.md)
    in the data/ethics directory if they do not already exist.
    """
    ethics_dir = get_ethics_dir()
    ethics_dir.mkdir(parents=True, exist_ok=True)

    consent_path = ethics_dir / "informed_consent.md"
    irb_path = ethics_dir / "irb_placeholder.md"

    if not consent_path.exists():
        consent_path.write_text(CONSENT_TEMPLATE, encoding="utf-8")
        print(f"Generated: {consent_path}")
    else:
        print(f"Skipped (exists): {consent_path}")

    if not irb_path.exists():
        irb_path.write_text(IRB_TEMPLATE, encoding="utf-8")
        print(f"Generated: {irb_path}")
    else:
        print(f"Skipped (exists): {irb_path}")

def main() -> None:
    """Entry point for the script."""
    ensure_ethics_artifacts()

if __name__ == "__main__":
    main()