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
from src.pipeline_orchestrator import ProductionPipelineOrchestrator

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
@click.option('--model', type=str,
              help='Specific model to use (e.g., microsoft/Phi-3-medium-4k-instruct)')
@click.option('--model-size-gb', type=float, default=None,
              help='Maximum model size in GB (default: 3.5 for GitHub Actions, 20 for local)')
@click.option('--project-id', type=str,
              help='Specific project ID to work on (optional)')
@click.option('--use-pipeline', is_flag=True,
              help='Use the new pipeline orchestrator')
@click.option('--dry-run', is_flag=True,
              help='Show what would be done without executing')
def main(github_token, hf_token, max_tasks, task, model, model_size_gb, project_id, use_pipeline, dry_run):
    """Run llmXive automation system"""
    
    logger.info("=== llmXive Automation Starting ===")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info(f"Max tasks: {max_tasks}")
    
    if task:
        logger.info(f"Specific task: {task}")
    if model:
        logger.info(f"Using model: {model}")
    if model_size_gb:
        logger.info(f"Max model size: {model_size_gb}GB")
    
    # Check for GitHub access
    if not github_token:
        logger.info("No GitHub token found. Attempting to use GitHub CLI (gh)...")
        logger.info("Make sure you're authenticated with: gh auth login")
    
    if dry_run:
        logger.info("[DRY RUN MODE - No changes will be made]")
        logger.info("Would perform the following:")
        logger.info("1. Load model from HuggingFace")
        logger.info("2. Analyze project state")
        logger.info("3. Generate and execute tasks")
        return
    
    try:
        # Determine model size limit
        if model_size_gb is None:
            # Default to 20GB for local, 3.5GB for CI
            import os
            model_size_gb = 3.5 if os.environ.get('CI') == 'true' else 20.0
            
        # Choose orchestrator based on flag
        if use_pipeline:
            logger.info("Using pipeline orchestrator...")
            orchestrator = ProductionPipelineOrchestrator(
                github_token=github_token,
                hf_token=hf_token,
                model_size_gb=model_size_gb,
                specific_model=model
            )
            
            # Run pipeline automation
            result = orchestrator.run_automation_cycle(
                max_tasks=max_tasks,
                specific_task=task,
                project_id=project_id
            )
            
        else:
            # Use original orchestrator
            logger.info("Using original orchestrator...")
            orchestrator = LLMXiveOrchestrator(
                github_token=github_token,
                hf_token=hf_token,
                model_size_gb=model_size_gb,
                specific_model=model
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
        
        # Log results (common for both orchestrators)
        if 'tasks_completed' in result:
            logger.info("=== Execution Summary ===")
            logger.info(f"Model used: {result.get('model_used', 'N/A')}")
            logger.info(f"Tasks completed: {result['tasks_completed']}/{result['total_tasks']}")
            logger.info(f"Tasks failed: {result['tasks_failed']}")
            logger.info(f"Execution time: {result['execution_time_seconds']:.2f} seconds")
            
            if project_id or result.get('project_id'):
                logger.info(f"Project: {project_id or result.get('project_id')}")
                
            if result['tasks_failed'] > 0:
                logger.warning("Some tasks failed. Check logs for details.")
        
        logger.info("Automation complete!")
        
    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()