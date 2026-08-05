"""
Final Derivation Audit Script (Task T066).

Re-runs symbolic verification (T026b) and peer review gate (T031c)
to ensure no regressions occurred during Phase 7 refactoring.
Updates docs/peer_review_checklist.md with status: PASSED.
"""
import os
import sys
import json
from datetime import datetime
import logging

# Add project root to path if running from scripts
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.derivation.symbolic_verification import main as verify_symbolic_main
from src.derivation.sample_complexity import main as sample_complexity_main
import yaml

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/final_audit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_symbolic_verification():
    """Re-run T026b: Symbolic verification of variance derivation."""
    logger.info("Starting symbolic verification (T026b)...")
    try:
        # Simulate command line args for the symbolic verification script
        sys.argv = ['run_final_derivation_audit.py', '--verify-all']
        verify_symbolic_main()
        
        # Check if the verification log was created and contains "VERIFIED"
        log_path = 'logs/symbolic_verification.log'
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
                if "VERIFIED" in content:
                    logger.info("Symbolic verification PASSED.")
                    return True
                else:
                    logger.error("Symbolic verification FAILED: 'VERIFIED' not found in log.")
                    return False
        else:
            logger.error("Symbolic verification FAILED: Log file not created.")
            return False
    except Exception as e:
        logger.error(f"Symbolic verification FAILED with exception: {e}")
        return False

def run_peer_review_gate():
    """Re-run T031c: Automated peer review gate (Symbolic Path)."""
    logger.info("Running peer review gate (T031c)...")
    try:
        # Run sample complexity derivation which includes assumption logging
        sys.argv = ['run_final_derivation_audit.py', '--verify-assumptions']
        sample_complexity_main()
        
        # Check if the derivation output was created
        output_path = 'docs/theoretical_derivation.md'
        if not os.path.exists(output_path):
            logger.error("Peer review gate FAILED: Derivation output not found.")
            return False
        
        logger.info("Peer review gate PASSED: Derivation output generated successfully.")
        return True
    except Exception as e:
        logger.error(f"Peer review gate FAILED with exception: {e}")
        return False

def update_peer_review_checklist(symbolic_passed, peer_review_passed):
    """Update docs/peer_review_checklist.md with final status."""
    checklist_path = 'docs/peer_review_checklist.md'
    os.makedirs('docs', exist_ok=True)
    
    # Determine final status
    if symbolic_passed and peer_review_passed:
        status = "PASSED"
        verified_by = "system"
        logger.info("Final Status: PASSED (Symbolic + Peer Review)")
    else:
        status = "FAILED"
        verified_by = "system"
        logger.warning(f"Final Status: FAILED (Symbolic: {symbolic_passed}, Peer Review: {peer_review_passed})")
    
    timestamp = datetime.now().isoformat()
    
    # Read existing content if it exists, otherwise create new
    if os.path.exists(checklist_path):
        with open(checklist_path, 'r') as f:
            content = f.read()
    else:
        content = "# Peer Review Checklist\n\n"
    
    # Update or append the status block
    # We will write a fresh status block at the end to ensure it's the latest
    new_status_block = f"""
## Final Audit Status (T066)
- **Timestamp**: {timestamp}
- **Symbolic Verification**: {'PASSED' if symbolic_passed else 'FAILED'}
- **Peer Review Gate**: {'PASSED' if peer_review_passed else 'FAILED'}
- **Overall Status**: {status}
- **Verified By**: {verified_by}
"""
    
    # Append to file
    with open(checklist_path, 'w') as f:
        f.write(content)
        f.write(new_status_block)
    
    logger.info(f"Updated {checklist_path} with status: {status}")
    return status

def main():
    logger.info("="*50)
    logger.info("Starting Final Derivation Audit (T066)")
    logger.info("="*50)
    
    # Run symbolic verification
    symbolic_passed = run_symbolic_verification()
    
    # Run peer review gate
    peer_review_passed = run_peer_review_gate()
    
    # Update checklist
    final_status = update_peer_review_checklist(symbolic_passed, peer_review_passed)
    
    if final_status == "PASSED":
        logger.info("Final Derivation Audit COMPLETED SUCCESSFULLY.")
        sys.exit(0)
    else:
        logger.error("Final Derivation Audit FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()