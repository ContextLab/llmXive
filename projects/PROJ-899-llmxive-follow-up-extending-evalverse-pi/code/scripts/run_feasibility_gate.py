import os
import sys
import logging
from pathlib import Path

from src.data.profiles import main as profiling_main, load_profiling_results, run_feasibility_gate
from src.utils import setup_logging, write_json


def main_wrapper() -> int:
    """
    Wrapper to run feasibility gate after profiling.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running feasibility gate...")
        
        # Load profiling results
        profiling_results = load_profiling_results()
        
        if not profiling_results:
            logger.error("No profiling results found.")
            return 1
        
        # Run feasibility gate
        gate_result = run_feasibility_gate(
            profiling_results,
            memory_threshold_gb=7.0,
            projected_hours_threshold=6.0
        )
        
        # Save gate result
        state_dir = Path(os.environ.get("STATE_ROOT", "data")) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        gate_path = state_dir / "feasibility_gate.json"
        write_json(str(gate_path), gate_result)
        
        logger.info(f"Feasibility gate: {'PASSED' if gate_result['gate_passed'] else 'FAILED'}")
        
        return 0 if gate_result['gate_passed'] else 1
        
    except Exception as e:
        logger.error(f"Feasibility gate failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main_wrapper())
