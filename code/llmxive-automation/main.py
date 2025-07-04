#!/usr/bin/env python3
"""Main entry point for llmXive automation"""

import os
import sys
import logging
from datetime import datetime
import click

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator import LLMXiveOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--github-token', envvar='GITHUB_TOKEN',
              help='GitHub access token (or set GITHUB_TOKEN env var)')
@click.option('--hf-token', envvar='HF_TOKEN',
              help='HuggingFace token (or set HF_TOKEN env var)')
@click.option('--max-tasks', default=5, type=int,
              help='Maximum number of tasks to execute')
@click.option('--task', type=str,
              help='Specific task type to run (optional)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without executing')
def main(github_token, hf_token, max_tasks, task, dry_run):
    """Run llmXive automation system"""
    
    logger.info("=== llmXive Automation Starting ===")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Max tasks: {max_tasks}")
    
    if task:
        logger.info(f"Specific task: {task}")
    
    # Validate tokens
    if not github_token:
        logger.error("GitHub token is required. Set GITHUB_TOKEN environment variable.")
        sys.exit(1)
    
    if dry_run:
        logger.info("[DRY RUN MODE - No changes will be made]")
        logger.info("Would perform the following:")
        logger.info("1. Load model from HuggingFace")
        logger.info("2. Analyze project state")
        logger.info("3. Generate and execute tasks")
        return
    
    try:
        # Initialize orchestrator
        logger.info("Initializing orchestrator...")
        orchestrator = LLMXiveOrchestrator(
            github_token=github_token,
            hf_token=hf_token
        )
        
        # Run automation cycle
        logger.info("Starting automation cycle...")
        
        if task:
            # Run specific task
            orchestrator.initialize_model()
            context = {}  # Could be enhanced to parse from command line
            
            result = orchestrator.executor.execute_task(task, context)
            
            if result.get('success'):
                logger.info(f"Task {task} completed successfully!")
                for key, value in result.items():
                    if key not in ['success', 'task_type', 'error']:
                        logger.info(f"  {key}: {value}")
            else:
                logger.error(f"Task {task} failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            # Run full automation cycle
            result = orchestrator.run_automation_cycle(max_tasks=max_tasks)
            
            # Log results
            logger.info("=== Execution Summary ===")
            logger.info(f"Model used: {result['model_used']}")
            logger.info(f"Tasks completed: {result['tasks_completed']}/{result['total_tasks']}")
            logger.info(f"Tasks failed: {result['tasks_failed']}")
            logger.info(f"Execution time: {result['execution_time_seconds']:.2f} seconds")
            
            if result['tasks_failed'] > 0:
                logger.warning("Some tasks failed. Check logs for details.")
        
        logger.info("Automation complete!")
        
    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()