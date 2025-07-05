"""Main runner for pipeline tests."""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

from .pipeline_orchestrator import PipelineTestOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_test_summary(result):
    """Print a summary of test results."""
    print("\n" + "=" * 80)
    print("PIPELINE TEST SUMMARY")
    print("=" * 80)
    
    status = "✅ PASSED" if result.success else "❌ FAILED"
    print(f"\nOverall Status: {status}")
    print(f"Steps Completed: {result.completed_steps}/{result.total_steps}")
    print(f"Duration: {result.duration_seconds:.1f} seconds")
    
    if result.validation_summary:
        print(f"\nValidation Summary:")
        print(f"  - Status: {result.validation_summary.get('overall_status', 'N/A')}")
        print(f"  - Pass Rate: {result.validation_summary.get('pass_rate', 0):.1f}%")
        print(f"  - Total Checks: {result.validation_summary.get('total_checks', 0)}")
        print(f"  - Errors: {result.validation_summary.get('errors', 0)}")
        print(f"  - Warnings: {result.validation_summary.get('warnings', 0)}")
    
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more")
    
    if result.warnings:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings[:5]:  # Show first 5
            print(f"  - {warning}")
        if len(result.warnings) > 5:
            print(f"  ... and {len(result.warnings) - 5} more")
    
    if result.final_state:
        print(f"\nFinal State:")
        print(f"  - Project: {result.final_state.project_id}")
        print(f"  - Stage: {result.final_state.current_stage.value}")
        print(f"  - Score: {result.final_state.current_score}")
        print(f"  - Artifacts: {list(result.final_state.artifacts.keys())}")
        print(f"  - History Events: {len(result.final_state.history)}")
    
    print("\n" + "=" * 80)


def main():
    """Main entry point for pipeline tests."""
    parser = argparse.ArgumentParser(
        description="Run llmXive pipeline tests"
    )
    parser.add_argument(
        "scenario",
        help="Path to scenario YAML file"
    )
    parser.add_argument(
        "--work-dir",
        help="Working directory for test artifacts",
        default=None
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        help="Save all test artifacts (default: cleanup after test)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file for detailed results (JSON)",
        default=None
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate scenario file
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        print(f"❌ Error: Scenario file not found: {scenario_path}")
        sys.exit(1)
    
    # Create work directory
    if args.work_dir:
        work_dir = Path(args.work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
    else:
        work_dir = None
    
    try:
        # Initialize orchestrator
        print(f"\n🚀 Starting pipeline test with scenario: {scenario_path}")
        print(f"Work directory: {work_dir or 'temporary'}")
        print("\n" + "-" * 80)
        
        orchestrator = PipelineTestOrchestrator(
            str(scenario_path),
            work_dir
        )
        
        # Run test
        start_time = datetime.now()
        result = orchestrator.run_test()
        
        # Print summary
        print_test_summary(result)
        
        # Save detailed results if requested
        if args.output:
            output_path = Path(args.output)
            output_data = {
                'scenario': str(scenario_path),
                'start_time': start_time.isoformat(),
                'result': {
                    'success': result.success,
                    'total_steps': result.total_steps,
                    'completed_steps': result.completed_steps,
                    'duration_seconds': result.duration_seconds,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'validation_summary': result.validation_summary
                }
            }
            
            if result.final_state:
                output_data['final_state'] = {
                    'project_id': result.final_state.project_id,
                    'stage': result.final_state.current_stage.value,
                    'score': result.final_state.current_score,
                    'artifacts': list(result.final_state.artifacts.keys()),
                    'history_length': len(result.final_state.history)
                }
            
            output_path.write_text(json.dumps(output_data, indent=2))
            print(f"\n💾 Detailed results saved to: {output_path}")
        
        # Cleanup or save artifacts
        if not args.save_artifacts and work_dir is None:
            # Clean up temporary directory
            import shutil
            if orchestrator.work_dir.exists():
                shutil.rmtree(orchestrator.work_dir)
                print("\n🧹 Cleaned up temporary artifacts")
        else:
            print(f"\n📁 Test artifacts saved in: {orchestrator.work_dir}")
        
        # Exit with appropriate code
        sys.exit(0 if result.success else 1)
        
    except Exception as e:
        logger.exception("Pipeline test failed with exception")
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(2)


if __name__ == "__main__":
    main()