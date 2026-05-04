"""
Run Constitution Principles I-VII re-check after Phase 1 design completion.

This script executes the constitution verification and saves the report
to specs/001-bayesian-nonparametrics-anomaly-detection/constitution_check.md

Usage: python run_constitution_check.py
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run constitution principles verification and save report."""
    logger.info("Starting Constitution Principles I-VII re-check after Phase 1")
    
    try:
        # Import verification functions from existing module
        from scripts.verify_constitution_principles import (
            VerificationResult,
            verify_principle_i_reproducibility,
            verify_principle_ii_task_isolation,
            verify_principle_iii_data_integrity,
            verify_principle_iv_path_conventions,
            verify_principle_v_project_structure,
            verify_principle_vi_elbo_logging,
            verify_principle_vii_api_consistency,
            generate_verification_report,
            save_report
        )
        
        logger.info("Verifying Principle I: Reproducibility")
        result_i = verify_principle_i_reproducibility(project_root)
        
        logger.info("Verifying Principle II: Task Isolation")
        result_ii = verify_principle_ii_task_isolation(project_root)
        
        logger.info("Verifying Principle III: Data Integrity")
        result_iii = verify_principle_iii_data_integrity(project_root)
        
        logger.info("Verifying Principle IV: Path Conventions")
        result_iv = verify_principle_iv_path_conventions(project_root)
        
        logger.info("Verifying Principle V: Project Structure")
        result_v = verify_principle_v_project_structure(project_root)
        
        logger.info("Verifying Principle VI: ELBO Logging")
        result_vi = verify_principle_vi_elbo_logging(project_root)
        
        logger.info("Verifying Principle VII: API Consistency")
        result_vii = verify_principle_vii_api_consistency(project_root)
        
        # Compile all results
        all_results = {
            'principle_i': result_i,
            'principle_ii': result_ii,
            'principle_iii': result_iii,
            'principle_iv': result_iv,
            'principle_v': result_v,
            'principle_vi': result_vi,
            'principle_vii': result_vii,
        }
        
        # Generate verification report
        report = generate_verification_report(
            all_results,
            project_root,
            timestamp=datetime.now()
        )
        
        # Save report to constitution_check.md
        constitution_check_path = project_root.parent / 'specs' / '001-bayesian-nonparametrics-anomaly-detection' / 'constitution_check.md'
        constitution_check_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(constitution_check_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"Constitution check report saved to: {constitution_check_path}")
        
        # Print summary to stdout
        print("=" * 60)
        print("CONSTITUTION PRINCIPLES VERIFICATION SUMMARY")
        print("=" * 60)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Stage: Post-Phase 1 Design Completion")
        print("-" * 60)
        
        total_passed = sum(1 for r in all_results.values() if r.get('passed', False))
        total_failed = sum(1 for r in all_results.values() if not r.get('passed', False))
        
        for name, result in all_results.items():
            status = "✓ PASS" if result.get('passed', False) else "✗ FAIL"
            print(f"{name.replace('_', ' ').title()}: {status}")
            if 'violations' in result and result['violations']:
                for violation in result['violations'][:3]:  # Show first 3
                    print(f"  - {violation}")
        
        print("-" * 60)
        print(f"Total: {total_passed} passed, {total_failed} failed out of 7 principles")
        print("=" * 60)
        
        # Return exit code based on results
        if total_failed > 0:
            logger.warning(f"{total_failed} principle(s) failed verification")
            return 1
        else:
            logger.info("All Constitution Principles verified successfully")
            return 0
            
    except ImportError as e:
        logger.error(f"Failed to import verification module: {e}")
        print(f"ERROR: Could not import verification functions: {e}")
        print("Please ensure code/scripts/verify_constitution_principles.py exists")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
