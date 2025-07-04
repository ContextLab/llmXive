#!/usr/bin/env python3
"""Command-line interface for llmXive automation"""

import os
import sys
import logging
import click
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.orchestrator import LLMXiveOrchestrator

# Load environment variables
load_dotenv()

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
@click.option('--task', type=click.Choice([
    'BRAINSTORM_IDEA', 'WRITE_TECHNICAL_DESIGN', 'REVIEW_TECHNICAL_DESIGN',
    'WRITE_IMPLEMENTATION_PLAN', 'REVIEW_IMPLEMENTATION_PLAN',
    'CONDUCT_LITERATURE_SEARCH', 'VALIDATE_REFERENCES',
    'WRITE_CODE', 'WRITE_TESTS', 'UPDATE_README_TABLE',
    'WRITE_ABSTRACT', 'WRITE_INTRODUCTION', 'WRITE_METHODS',
    'WRITE_RESULTS', 'WRITE_DISCUSSION',
    'REVIEW_PAPER', 'REVIEW_CODE',
    'CHECK_PROJECT_STATUS', 'CREATE_ISSUE_COMMENT',
    'GENERATE_HELPER_FUNCTION', 'IDENTIFY_IMPROVEMENTS'
]), help='Run a specific task type')
@click.option('--issue', type=int, help='Issue number for task context')
@click.option('--project-id', help='Project ID for task context')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
@click.option('--model-cache', type=click.Path(),
              default=os.path.expanduser("~/.cache/huggingface"),
              help='Directory for model cache')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--model', type=str, help='Specific model to use')
@click.option('--model-size-gb', type=float, help='Maximum model size in GB')
def main(github_token, hf_token, max_tasks, task, issue, project_id, 
         dry_run, model_cache, verbose, model, model_size_gb):
    """Run llmXive automation locally"""
    
    # Check for GitHub access
    if not github_token:
        click.echo("Note: No GitHub token found. Attempting to use GitHub CLI (gh)...")
        click.echo("Make sure you're authenticated with: gh auth login")
        
    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Show configuration
    click.echo("=== llmXive Automation ===")
    click.echo(f"Max tasks: {max_tasks}")
    click.echo(f"Specific task: {task or 'Auto'}")
    click.echo(f"Model cache: {model_cache}")
    if model:
        click.echo(f"Specific model: {model}")
    if model_size_gb:
        click.echo(f"Max model size: {model_size_gb} GB")
    
    if dry_run:
        click.echo("\n[DRY RUN MODE - No changes will be made]")
        click.echo("\nWould execute the following:")
        click.echo(f"- Initialize model from HuggingFace")
        click.echo(f"- Analyze project state")
        
        if task:
            click.echo(f"- Execute task: {task}")
            if issue:
                click.echo(f"  - Issue context: #{issue}")
            if project_id:
                click.echo(f"  - Project ID: {project_id}")
        else:
            click.echo(f"- Generate and execute up to {max_tasks} prioritized tasks")
            
        return
        
    # Initialize orchestrator
    try:
        click.echo("\nInitializing orchestrator...")
        orchestrator = LLMXiveOrchestrator(
            github_token=github_token,
            hf_token=hf_token,
            model_cache_dir=model_cache,
            model_size_gb=model_size_gb,
            specific_model=model
        )
        
        # Build task context if specific task
        context = {}
        if issue:
            context['issue_number'] = issue
        if project_id:
            context['project_id'] = project_id
            
        # Run automation
        click.echo("Starting automation cycle...")
        
        if task:
            # Run specific task
            orchestrator.initialize_model()
            result = orchestrator.executor.execute_task(task, context)
            
            if result.get('success'):
                click.echo(f"\n✅ Task completed successfully!")
                
                # Show key outputs
                for key, value in result.items():
                    if key not in ['success', 'task_type', 'error']:
                        click.echo(f"  - {key}: {value}")
            else:
                click.echo(f"\n❌ Task failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            # Run full automation cycle
            result = orchestrator.run_automation_cycle(max_tasks=max_tasks)
            
            # Show results
            click.echo("\n=== Execution Summary ===")
            click.echo(f"Model used: {result['model_used']}")
            click.echo(f"Tasks completed: {result['tasks_completed']}/{result['total_tasks']}")
            click.echo(f"Tasks failed: {result['tasks_failed']}")
            click.echo(f"Execution time: {result['execution_time_seconds']:.2f} seconds")
            
            if result['tasks_failed'] > 0:
                click.echo("\n⚠️  Some tasks failed. Check logs for details.")
                
        click.echo("\n✨ Automation complete!")
        
    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        click.echo(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()