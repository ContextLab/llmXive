"""
Generates ethics artifacts for the Visual Detail and False Memory study.
Creates GDPR-compliant templates for Informed Consent and IRB placeholders.
"""
import os
from pathlib import Path

# Ensure we are running from the project root context or handle relative paths correctly
# Based on task description, artifacts go to data/ethics/
def main():
    # Define output paths relative to project root
    # Assuming this script is run from the project root or code/ directory
    # We will resolve relative to the script's parent if in code/ethics/
    script_dir = Path(__file__).parent
    # If the script is in code/ethics/, we go up to project root
    if script_dir.name == "ethics" and script_dir.parent.name == "code":
        project_root = script_dir.parent.parent
    else:
        # Fallback: assume current working directory is project root
        project_root = Path.cwd()

    ethics_dir = project_root / "data" / "ethics"
    ethics_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate Informed Consent Template
    consent_content = """# Informed Consent Form

**Study Title:** The Impact of Visual Detail on False Memory Susceptibility
**Principal Investigator:** [PI Name]
**Institution:** [Institution Name]
**Contact Information:** [Email] | [Phone]

## 1. Introduction
You are invited to participate in a research study investigating how visual detail in images affects the formation of false memories. This document explains the purpose of the study, what your participation involves, and your rights as a participant. Please read this form carefully and ask any questions before deciding whether to participate.

## 2. Purpose of the Study
The purpose of this research is to understand how the level of visual detail in an image influences a person's susceptibility to forming false memories about that image. Specifically, we are examining whether images with enhanced detail lead to higher or lower rates of false recognition compared to images with reduced detail.

## 3. Procedures
If you agree to participate, you will be asked to:
1. View a series of baseline images.
2. Complete a brief distractor task (arithmetic problems) to clear short-term memory.
3. Answer recognition questions regarding details that were either present (true) or absent (false/lure) in the original images.
4. Provide demographic information (age range, gender, etc.) for analysis purposes.

The entire session will take approximately 20-30 minutes.

## 4. Risks and Discomforts
The risks associated with this study are minimal and comparable to everyday life. The primary risk is the potential for temporary confusion or mild frustration during the distractor task. The study involves the formation of false memories, which is a temporary cognitive state and poses no long-term psychological harm.

## 5. Benefits
There are no direct benefits to you as a participant. However, the data collected will contribute to the scientific understanding of human memory and visual perception, potentially aiding in the development of more reliable eyewitness testimony protocols.

## 6. Confidentiality and Data Protection (GDPR Compliance)
Your data will be handled in strict accordance with the General Data Protection Regulation (GDPR):
- **Data Minimization:** Only data necessary for the research objectives will be collected.
- **Anonymization:** All personal identifiers will be removed. Participants will be assigned a unique, random ID code.
- **Storage:** Data will be stored on encrypted, password-protected servers accessible only to the research team.
- **Retention:** Data will be retained for [Number] years as required by institutional policy, after which it will be securely destroyed.
- **Right to Withdraw:** You have the right to withdraw from the study at any time without penalty. If you withdraw, your data will be deleted immediately, provided it has not yet been anonymized and aggregated.

## 7. Voluntary Participation
Participation in this study is entirely voluntary. You may decline to answer any specific question or withdraw from the study at any time without consequence.

## 8. Contact Information
If you have questions about the study, please contact:
- **Researcher:** [Name], [Email]
- **Institutional Review Board (IRB):** [IRB Email] | [IRB Phone]

## 9. Consent Statement
By proceeding to the next screen, I acknowledge that:
- I have read and understood the information provided above.
- I have had the opportunity to ask questions.
- I voluntarily agree to participate in this study.
- I understand that my participation is anonymous and my data will be handled securely.

[ ] I consent to participate.

---
*Generated on: [Date]*
*Protocol ID: [IRB Protocol Number]*
"""

    consent_path = ethics_dir / "informed_consent.md"
    with open(consent_path, "w", encoding="utf-8") as f:
        f.write(consent_content)
    print(f"Created: {consent_path}")

    # 2. Generate IRB Placeholder Template
    irb_content = """# IRB Application Placeholder

**Study Title:** The Impact of Visual Detail on False Memory Susceptibility
**Protocol ID:** [Pending Assignment]
**Application Date:** [Date]
**Principal Investigator:** [PI Name]
**Department:** [Department Name]

## 1. Study Summary
This study investigates the relationship between visual detail complexity and false memory susceptibility. Participants view manipulated images (enhanced or reduced detail) and are tested on their recognition of true vs. false details.

## 2. Methodology
- **Participants:** N = [Calculated Sample Size] adults recruited via [Recruitment Method].
- **Procedure:** Participants complete a computerized task involving image viewing, distractor tasks, and recognition quizzes.
- **Data Collection:** Responses are recorded digitally and stored anonymously.

## 3. Ethical Considerations
- **Risk Level:** Minimal Risk.
- **Vulnerable Populations:** None.
- **Deception:** None. The study does not involve deception; participants are informed about the general nature of memory research without revealing specific hypotheses to prevent bias.
- **Debriefing:** Participants will be fully debriefed at the end of the session regarding the specific hypotheses and the nature of false memories.

## 4. Data Management Plan
- **Storage:** Encrypted server at [Institution Name].
- **Access:** Restricted to the core research team.
- **Anonymization:** Direct identifiers will be replaced with random IDs upon collection.
- **GDPR Compliance:** The study adheres to GDPR principles of lawfulness, fairness, transparency, and data minimization.

## 5. Informed Consent Process
Consent will be obtained digitally prior to the start of the session. Participants must actively check a box indicating they have read and understood the consent form.

## 6. Risk Mitigation
- Participants may stop the session at any time.
- No sensitive or personally identifiable information (PII) will be collected.
- Psychological discomfort is minimal and addressed via debriefing.

## 7. Approval Checklist
- [ ] Protocol reviewed by IRB Chair
- [ ] Informed consent form attached
- [ ] Data management plan approved
- [ ] Recruitment materials reviewed
- [ ] Debriefing script attached

---
**IRB Decision:** [Pending / Approved / Modifications Required]
**Expiration Date:** [Date]
**Signature:** _________________________
"""

    irb_path = ethics_dir / "irb_placeholder.md"
    with open(irb_path, "w", encoding="utf-8") as f:
        f.write(irb_content)
    print(f"Created: {irb_path}")

    print("Ethics artifacts generation complete.")

if __name__ == "__main__":
    main()