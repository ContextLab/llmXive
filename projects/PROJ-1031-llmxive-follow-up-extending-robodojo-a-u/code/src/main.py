"""
code/src/main.py

Orchestration script for the llmXive RoboDojo extension pipeline.
Chains data loading, symbolic state mapping, planning, execution, and logging.
"""

import os
import sys
import logging
import time
from typing import Optional, Dict, Any

# Add src to path for imports if running as script
if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

from src.config import BASE_DIR, PLANNING_TIMEOUT_S, SEED
from src.data_loader import stream_robodojo_tasks
from src.state_mapper import StateMapper, create_symbolic_state
from src.vision_encoder import create_vision_encoder
from src.planner import AStarPlanner, create_planner, run_planning_pipeline
from src.executor import Executor, run_executor_pipeline
from src.oracle_executor import OracleExecutor, run_oracle_pipeline
from src.controller_adapter import run_adapter_pipeline
from src.metrics_logger import MetricsLogger, create_metrics_logger, ResourceLimitExceeded
from src.stats_analysis import run_full_analysis, generate_statistical_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_orchestrator(
    run_adapter: bool = False,
    run_planner: bool = True,
    run_executor: bool = False,
    run_oracle: bool = False,
    run_analysis: bool = False,
    max_tasks: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main orchestration entry point.
    Chains the pipeline stages based on flags.
    """
    logger.info("Starting llmXive RoboDojo Orchestration Pipeline")
    logger.info(f"Base Directory: {BASE_DIR}")
    logger.info(f"Seed: {SEED}")

    metrics_logger = create_metrics_logger()
    start_time = time.time()

    try:
        # 1. Data Loading & Vision Encoding
        logger.info("Phase 1: Initializing Data Loader and Vision Encoder")
        vision_encoder = create_vision_encoder()
        task_stream = stream_robodojo_tasks()
        
        processed_tasks = []
        for i, task in enumerate(task_stream):
            if max_tasks and i >= max_tasks:
                logger.info(f"Reached max_tasks limit ({max_tasks}). Stopping data stream.")
                break
            
            # Map to symbolic state
            symbolic_state = create_symbolic_state(task, vision_encoder)
            processed_tasks.append({
                "raw": task,
                "symbolic": symbolic_state
            })
        
        logger.info(f"Loaded and mapped {len(processed_tasks)} tasks to symbolic states.")

        # 2. Controller Adapter (Optional/Prerequisite for Execution)
        if run_adapter:
            logger.info("Phase 2: Running Controller Adapter Pipeline (T010)")
            try:
                adapter_weights_path = run_adapter_pipeline()
                logger.info(f"Adapter pipeline completed. Weights saved to: {adapter_weights_path}")
            except Exception as e:
                logger.error(f"Adapter pipeline failed: {e}")
                if run_executor:
                    logger.warning("Execution requested but adapter failed. Skipping execution.")
                    run_executor = False

        # 3. Planning (T015, T022)
        symbolic_results = []
        if run_planner:
            logger.info("Phase 3: Running Symbolic Planning Pipeline (T015)")
            planner = create_planner()
            
            for task_data in processed_tasks:
                task_id = task_data["raw"].get("task_id", "unknown")
                logger.info(f"Planning for task: {task_id}")
                
                try:
                    action_sequence, plan_time, memory_usage = run_planning_pipeline(
                        task_data["symbolic"], 
                        planner, 
                        timeout_s=PLANNING_TIMEOUT_S
                    )
                    symbolic_results.append({
                        "task_id": task_id,
                        "action_sequence": action_sequence,
                        "planning_time_s": plan_time,
                        "peak_memory_mb": memory_usage,
                        "success": True
                    })
                    logger.info(f"Plan generated for {task_id} in {plan_time:.2f}s.")
                except ResourceLimitExceeded as e:
                    logger.error(f"Resource limit exceeded for {task_id}: {e}")
                    symbolic_results.append({
                        "task_id": task_id,
                        "success": False,
                        "error": str(e)
                    })
                except Exception as e:
                    logger.error(f"Planning failed for {task_id}: {e}")
                    symbolic_results.append({
                        "task_id": task_id,
                        "success": False,
                        "error": str(e)
                    })

        # 4. Execution (T021, T024, T025, T026)
        execution_results = []
        if run_executor and symbolic_results:
            logger.info("Phase 4: Running Real-World Execution Pipeline (T021-T026)")
            executor = Executor()
            
            for plan_res in symbolic_results:
                if not plan_res.get("success"):
                    continue
                
                task_id = plan_res["task_id"]
                logger.info(f"Executing plan for task: {task_id}")
                
                try:
                    outcome = executor.execute(plan_res["action_sequence"])
                    execution_results.append(outcome)
                    logger.info(f"Execution outcome for {task_id}: {outcome.success}")
                except Exception as e:
                    logger.error(f"Execution failed for {task_id}: {e}")
                    execution_results.append({
                        "task_id": task_id,
                        "success": False,
                        "failure_mode": "Hardware Error",
                        "error": str(e)
                    })

        # 5. Oracle Execution (T037, T038) - Optional
        oracle_results = []
        if run_oracle and symbolic_results:
            logger.info("Phase 5: Running Oracle Execution Pipeline (T037-T038)")
            oracle = OracleExecutor()
            
            for plan_res in symbolic_results:
                if not plan_res.get("success"):
                    continue
                
                task_id = plan_res["task_id"]
                logger.info(f"Running Oracle for task: {task_id}")
                
                try:
                    outcome = oracle.execute(plan_res["action_sequence"])
                    oracle_results.append(outcome)
                except Exception as e:
                    logger.error(f"Oracle execution failed for {task_id}: {e}")

        # 6. Statistical Analysis (T032-T036)
        if run_analysis:
            logger.info("Phase 6: Running Statistical Analysis (T032-T036)")
            try:
                # Ensure execution logs exist if requested
                if not execution_results and run_executor:
                    logger.warning("No execution results found for analysis.")
                
                report_data = run_full_analysis(
                    symbolic_results=symbolic_results,
                    execution_results=execution_results,
                    oracle_results=oracle_results
                )
                generate_statistical_report(report_data)
                logger.info("Statistical report generated successfully.")
            except Exception as e:
                logger.error(f"Statistical analysis failed: {e}")

        total_time = time.time() - start_time
        logger.info(f"Pipeline completed in {total_time:.2f} seconds.")
        
        return {
            "tasks_processed": len(processed_tasks),
            "plans_generated": len([r for r in symbolic_results if r.get("success")]),
            "executions_completed": len(execution_results),
            "total_time_s": total_time
        }

    except Exception as e:
        logger.critical(f"Pipeline orchestration failed: {e}", exc_info=True)
        raise

def main():
    """
    CLI entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="llmXive RoboDojo Orchestration Script")
    parser.add_argument("--adapter", action="store_true", help="Run controller adapter training")
    parser.add_argument("--planner", action="store_true", default=True, help="Run symbolic planner")
    parser.add_argument("--executor", action="store_true", help="Run real-world execution")
    parser.add_argument("--oracle", action="store_true", help="Run oracle execution")
    parser.add_argument("--analysis", action="store_true", help="Run statistical analysis")
    parser.add_argument("--max-tasks", type=int, default=None, help="Limit number of tasks to process")
    
    args = parser.parse_args()
    
    run_orchestrator(
        run_adapter=args.adapter,
        run_planner=args.planner,
        run_executor=args.executor,
        run_oracle=args.oracle,
        run_analysis=args.analysis,
        max_tasks=args.max_tasks
    )

if __name__ == "__main__":
    main()