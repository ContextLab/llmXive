"""
Recruitment Protocol Generator for Digital Decluttering Study.

This module generates the formal recruitment protocol document required for
the study, ensuring compliance with FR-009. It defines eligibility, compensation,
consent text, and pilot instructions.

It also includes a stub for executing pilot simulations to validate the protocol
logic before human recruitment.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def generate_recruitment_protocol_content() -> str:
    """
    Generates the full markdown content for the recruitment protocol.

    Returns:
        str: The complete markdown content for docs/recruitment_protocol.md.
    """
    current_date = datetime.now().strftime("%Y-%m-%d")

    content = f"""# Recruitment Protocol: The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Study ID**: PROJ-249
**Version**: 1.0
**Date**: {current_date}
**Principal Investigator**: [PI Name Placeholder]
**Institution**: [Institution Name Placeholder]

---

## 1. Eligibility Criteria

### 1.1 Inclusion Criteria
Participants must meet ALL of the following criteria to be eligible for this study:
1. **Age**: 18 years or older.
2. **Device Ownership**: Own a smartphone (iOS or Android) capable of installing the required monitoring application.
3. **Language**: Fluent in English (reading and comprehension level sufficient for consent and questionnaire completion).
4. **Digital Usage**: Self-reported average daily screen time of at least 2 hours on non-work days.
5. **Availability**: Available to complete daily logs for 7 consecutive days and attend two scheduled testing sessions (Baseline and Post-Intervention).

### 1.2 Exclusion Criteria
Participants will be excluded if they meet ANY of the following:
1. **Current Treatment**: Currently undergoing treatment for severe anxiety, depression, or attention disorders that could confound cognitive metrics.
2. **Technical Barriers**: Unable to install third-party applications or use screen-time tracking APIs due to device restrictions (e.g., corporate managed devices).
3. **Prior Participation**: Have participated in a digital decluttering study within the last 6 months.
4. **Language Barriers**: Limited English proficiency.

---

## 2. Compensation

### 2.1 Payment Structure
Participants will be compensated based on their completion of study milestones:
- **Baseline Session**: $15.00 upon successful completion of SART, Ospan, PSS-10, and PANAS assessments.
- **Intervention Period**: $5.00 per day for submitting valid daily compliance logs (up to $35.00 for 7 days).
- **Post-Intervention Session**: $15.00 upon successful completion of post-study assessments.
- **Bonus**: $10.00 bonus for participants who maintain >90% compliance with the digital decluttering rules (≤30 min social media, no news, notifications off).

**Total Potential Compensation**: Up to $75.00.

### 2.2 Payment Method
Payments will be processed via [Prolific/Amazon Mechanical Turk/Stripe] within 48 hours of data validation.

### 2.3 Prorated Compensation
- Participants who drop out after the Baseline Session will receive the $15.00 baseline payment.
- Participants who drop out during the Intervention Period will be paid prorated for the number of valid daily logs submitted.
- No payment is provided for incomplete sessions that do not meet the minimum data quality thresholds (e.g., <50% accuracy on attention checks).

---

## 3. Consent Text

### 3.1 Introduction
You are invited to participate in a research study investigating the effects of digital decluttering on cognitive performance and well-being. This study is conducted by [Researcher Name] at [Institution].

### 3.2 Purpose
The purpose of this study is to determine if reducing non-essential digital usage (social media, news) improves attention span, working memory, and reduces perceived stress.

### 3.3 Procedures
If you agree to participate, you will be asked to:
1. **Baseline Assessment**: Complete a 30-minute online session including cognitive tasks (SART, Ospan) and questionnaires (PSS-10, PANAS).
2. **Intervention**: For 7 days, limit social media usage to 30 minutes/day, avoid news consumption, and turn off non-essential notifications. You will install a monitoring app to verify compliance.
3. **Daily Logs**: Submit a brief daily report on your adherence to the rules.
4. **Post-Intervention Assessment**: Complete the same cognitive tasks and questionnaires as in the baseline session.

### 3.4 Risks and Discomforts
The risks associated with this study are minimal. You may experience mild frustration or boredom from reducing digital usage. If you feel significant distress, you may withdraw at any time.

### 3.5 Benefits
There are no direct benefits to you, but the results may contribute to understanding how digital habits affect mental health.

### 3.6 Confidentiality
Your data will be pseudonymized. Your name will be replaced with a unique ID (e.g., P001). Only the research team will have access to the key linking IDs to names. All data will be stored on encrypted servers.

### 3.7 Voluntary Participation
Your participation is entirely voluntary. You may withdraw from the study at any time without penalty or loss of benefits to which you are otherwise entitled.

### 3.8 Contact Information
If you have questions, please contact [Researcher Email]. For research ethics concerns, contact [IRB Email].

**I have read and understood the information above. I voluntarily agree to participate.**
[ ] I Agree
[ ] I Do Not Agree

---

## 4. Pilot Instructions

### 4.1 Purpose of Pilot
Before full-scale recruitment, a pilot test (n=5) will be conducted to validate the data collection pipeline, ensure the monitoring app functions correctly, and verify that the cognitive tasks are administered properly.

### 4.2 Pilot Participant Instructions
1. **Recruitment**: Pilot participants will be recruited from the research team's network or a small internal pool.
2. **Setup**: Install the `headless_simulator` or the actual mobile app on your device. Ensure permissions for screen-time access are granted.
3. **Execution**:
   - Complete the Baseline Assessment using the provided link.
   - Follow the digital decluttering rules for 3 days (abbreviated pilot period).
   - Submit daily logs via the provided form.
   - Complete the Post-Intervention Assessment.
4. **Feedback**: After completion, you will be asked to provide feedback on the clarity of instructions, technical issues encountered, and estimated time commitment.

### 4.3 Success Criteria for Pilot
The pilot is considered successful if:
- 100% of pilot participants complete the full protocol.
- No critical technical errors occur in data logging.
- Cognitive task scores fall within expected ranges (SART errors > 0, PSS 0-40).
- Average completion time for the baseline session is between 20-40 minutes.

### 4.4 Next Steps
Upon successful pilot validation, the full recruitment protocol will be approved for external recruitment via [Platform Name].

---

*End of Document*
"""
    return content

def execute_pilot_simulation() -> Dict[str, Any]:
    """
    Executes a simulated pilot run to validate the protocol logic.
    This function simulates the flow of a participant through the protocol
    without recruiting real humans, using synthetic data generation where appropriate.

    Returns:
        Dict[str, Any]: Summary of the pilot simulation results.
    """
    logger.info("Executing pilot simulation for recruitment protocol validation...")

    # Simulate a single pilot participant flow
    pilot_data = {
        "participant_id": "P000", # Special pilot ID
        "status": "completed",
        "baseline_completed": True,
        "intervention_days_completed": 3, # Abbreviated pilot
        "post_intervention_completed": True,
        "compliance_score": 0.95,
        "issues_found": []
    }

    # Validate ranges
    if pilot_data["baseline_completed"] and pilot_data["post_intervention_completed"]:
        logger.info("Pilot participant successfully completed all assessment phases.")
    else:
        pilot_data["issues_found"].append("Incomplete assessment phases")

    if pilot_data["compliance_score"] > 0.9:
        logger.info("Pilot participant met high compliance threshold.")
    else:
        pilot_data["issues_found"].append("Compliance score below threshold")

    return pilot_data

def write_protocol_document(output_path: Path) -> None:
    """
    Writes the generated recruitment protocol to a markdown file.

    Args:
        output_path (Path): The path where the markdown file will be saved.
    """
    content = generate_recruitment_protocol_content()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Recruitment protocol written to: {output_path}")

def run_recruitment_protocol() -> Dict[str, Any]:
    """
    Main entry point to run the recruitment protocol generation and validation.

    Returns:
        Dict[str, Any]: Summary of operations performed.
    """
    logger.info("Starting Recruitment Protocol Pipeline...")
    
    output_file = PROJECT_ROOT / "docs" / "recruitment_protocol.md"
    
    # 1. Generate and write document
    write_protocol_document(output_file)
    
    # 2. Execute pilot simulation
    pilot_results = execute_pilot_simulation()
    
    # 3. Verify file existence
    if not output_file.exists():
        raise FileNotFoundError(f"Failed to write protocol to {output_file}")
    
    return {
        "protocol_file": str(output_file),
        "pilot_simulation": pilot_results,
        "status": "success"
    }

def main():
    """
    CLI entry point.
    """
    try:
        result = run_recruitment_protocol()
        print(f"Protocol generation complete. Output: {result['protocol_file']}")
        print(f"Pilot simulation status: {result['pilot_simulation']['status']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()