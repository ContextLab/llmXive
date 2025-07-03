"""CLI entry point for llmXive automation"""

import click
import os
import sys
from .main import LLMXiveAutomation
from .task_orchestrator import TaskType


@click.command()
@click.option('--mode', 
              type=click.Choice(['auto', 'interactive', 'single-task']), 
              default='auto',
              help='Execution mode')
@click.option('--task', 
              type=str, 
              help='Specific task to execute (for single-task mode)')
@click.option('--model', 
              type=str, 
              help='Override model selection')
@click.option('--dry-run', 
              is_flag=True, 
              help='Preview actions without executing')
@click.option('--verbose', 
              is_flag=True, 
              help='Enable verbose logging')
def main(mode, task, model, dry_run, verbose):
    """Run llmXive automation system
    
    This tool automates scientific research tasks including:
    - Brainstorming new research ideas
    - Developing technical designs
    - Writing reviews
    - Implementing research code
    - Generating papers
    - Validating references
    
    Examples:
        # Run full automation cycle
        python -m llmxive_automation
        
        # Run specific task
        python -m llmxive_automation --mode single-task --task brainstorm_ideas
        
        # Dry run with specific model
        python -m llmxive_automation --model microsoft/phi-2 --dry-run
        
        # Interactive mode
        python -m llmxive_automation --mode interactive
    """
    
    # Set up logging
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check environment
    if not os.getenv("GITHUB_TOKEN"):
        click.echo("ERROR: GITHUB_TOKEN environment variable not set", err=True)
        click.echo("Please set: export GITHUB_TOKEN=your_token", err=True)
        sys.exit(1)
    
    # Validate task if specified
    if mode == "single-task" and task:
        valid_tasks = [t.value for t in TaskType]
        if task not in valid_tasks:
            click.echo(f"ERROR: Invalid task '{task}'", err=True)
            click.echo(f"Valid tasks: {', '.join(valid_tasks)}", err=True)
            sys.exit(1)
    
    # Show configuration
    click.echo("llmXive Automation System")
    click.echo("=" * 40)
    click.echo(f"Mode: {mode}")
    if task:
        click.echo(f"Task: {task}")
    if model:
        click.echo(f"Model override: {model}")
    if dry_run:
        click.echo("DRY RUN MODE - No changes will be made")
    click.echo("=" * 40)
    click.echo()
    
    # Run automation
    try:
        automation = LLMXiveAutomation(
            mode=mode,
            task_override=task,
            model_override=model,
            dry_run=dry_run
        )
        automation.run()
        
        click.echo("\n✅ Automation completed successfully!")
        
    except Exception as e:
        click.echo(f"\n❌ Automation failed: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()