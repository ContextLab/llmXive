import os
import sys
from pathlib import Path
from typing import Optional

from config import get_project_root, get_ethics_dir, get_data_dir
from utils.logging import get_logger

logger = get_logger(__name__)

def generate_informed_consent_content() -> str:
    """Generate content for the informed consent document."""
    return """
    INFORMED CONSENT FORM

    Study Title: The Impact of Visual Detail on False Memory Susceptibility

    Principal Investigator: [Research Team]
    Institution: [Institution Name]

    Introduction:
    You are invited to participate in a research study. This form provides information 
    to help you decide whether to participate. Please read carefully.

    Purpose:
    This study investigates how visual detail in images affects the formation of false 
    memories. Participants will view images and answer questions about details they may 
    or may not have seen.

    Procedures:
    - You will view a series of images for 10 seconds each.
    - You will complete a 2-minute distractor task.
    - You will answer recognition questions about the images.
    - The session will last approximately 15-20 minutes.

    Risks:
    There are minimal risks. You may experience mild fatigue or boredom.

    Benefits:
    You will contribute to scientific understanding of memory processes.

    Confidentiality:
    Your data will be anonymized and stored securely. No personally identifiable 
    information will be published.

    Voluntary Participation:
    Your participation is voluntary. You may withdraw at any time without penalty.

    Contact:
    For questions, contact [Research Team Email].

    By signing below, you indicate your voluntary agreement to participate.

    _________________________
    Participant Signature

    _________________________
    Date
    """

def generate_irb_placeholder_content() -> str:
    """Generate placeholder content for IRB approval document."""
    return """
    IRB APPROVAL DOCUMENT

    Study ID: PROJ-317-the-impact-of-visual-detail-on-false-mem
    Study Title: The Impact of Visual Detail on False Memory Susceptibility

    Approval Status: [PENDING / APPROVED]
    Approval Date: [DATE]
    Expiration Date: [DATE]
    IRB Reference Number: [NUMBER]

    This document serves as a placeholder for the official IRB approval. 
    Recruitment and data collection may not begin until official approval 
    is obtained and documented.

    Notes:
    - This is a simulated document for development purposes.
    - In a real study, the official IRB letter must be attached.
    - All participants must sign the informed consent form.
    """

def ensure_ethics_artifacts(
    mode: str = "pre-bundled",
    count: int = 30,
    seed: int = 42
) -> bool:
    """
    Ensure ethics artifacts exist.

    Args:
        mode: 'pre-bundled' (requires IRB) or 'mock' (CI mode).
        count: Number of mock participants (if mode is 'mock').
        seed: Random seed for reproducibility.

    Returns:
        True if ethics requirements are met, False otherwise.
    """
    ethics_dir = get_ethics_dir()
    ethics_dir.mkdir(parents=True, exist_ok=True)

    irb_path = ethics_dir / "irb_approval_final.pdf"
    consent_path = ethics_dir / "informed_consent.txt"
    placeholder_path = ethics_dir / "irb_placeholder.txt"

    if mode == "pre-bundled":
        # Check for real IRB approval
        if not irb_path.exists():
            logger.error(
                f"CRITICAL: No real IRB approval document found at {irb_path}. "
                "Recruitment cannot begin. Please obtain IRB approval for "
                "PROJ-317-the-impact-of-visual-detail-on-false-mem and place "
                "the document in the ethics directory before proceeding."
            )
            return False

        logger.info("IRB approval document found. Proceeding.")

    elif mode == "mock":
        # Generate placeholder for CI/mock mode
        logger.warning("Running in mock mode. No real IRB approval required.")
        
        # Write placeholder
        with open(placeholder_path, 'w') as f:
            f.write(generate_irb_placeholder_content())
        
        logger.info(f"Created IRB placeholder at {placeholder_path}")

    else:
        logger.error(f"Unknown mode: {mode}. Use 'pre-bundled' or 'mock'.")
        return False

    # Always generate consent form
    with open(consent_path, 'w') as f:
        f.write(generate_informed_consent_content())

    logger.info(f"Created informed consent at {consent_path}")

    return True

def main():
    """CLI entry point for ethics artifact generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate ethics artifacts")
    parser.add_argument('--mode', type=str, default="mock", 
                        choices=['pre-bundled', 'mock'],
                        help='Mode: pre-bundled (requires IRB) or mock (CI)')
    parser.add_argument('--count', type=int, default=30, help='Number of mock participants')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')

    args = parser.parse_args()

    success = ensure_ethics_artifacts(
        mode=args.mode,
        count=args.count,
        seed=args.seed
    )

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())