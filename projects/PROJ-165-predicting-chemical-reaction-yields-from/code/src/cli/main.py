"""
CLI entry point for the llmXive research pipeline.

Provides subcommands for state management and future pipeline orchestration.
"""
import argparse
import sys
import logging
from pathlib import Path

# Import from existing API surface
from src.utils.state_manager import update_state, load_state, log_task_start, log_task_complete, reset_state
from src.utils.seeds import set_seed
from src.utils.validators import load_yaml, ValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def parse_args(args=None):
    """
    Parse command line arguments.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv[1:])
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog='llmXive',
        description='Automated science pipeline for chemical reaction yield prediction'
    )
    
    # Global options
    parser.add_argument(
        '--config',
        type=str,
        default='code/src/config/defaults.yaml',
        help='Path to configuration file (default: code/src/config/defaults.yaml)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # update-state command
    update_parser = subparsers.add_parser(
        'update-state',
        help='Update project state with current task and timestamps'
    )
    update_parser.add_argument(
        '--task-id',
        type=str,
        required=True,
        help='Task ID to log (e.g., T009)'
    )
    update_parser.add_argument(
        '--status',
        type=str,
        choices=['start', 'complete', 'fail'],
        default='complete',
        help='Task status to log (default: complete)'
    )
    update_parser.add_argument(
        '--state-file',
        type=str,
        default='state/project_state.json',
        help='Path to state file (default: state/project_state.json)'
    )
    
    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Display current project state summary'
    )
    status_parser.add_argument(
        '--state-file',
        type=str,
        default='state/project_state.json',
        help='Path to state file (default: state/project_state.json)'
    )
    
    # reset-state command
    reset_parser = subparsers.add_parser(
        'reset-state',
        help='Reset project state to initial values'
    )
    reset_parser.add_argument(
        '--state-file',
        type=str,
        default='state/project_state.json',
        help='Path to state file (default: state/project_state.json)'
    )
    reset_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm reset operation'
    )
    
    return parser.parse_args(args)


def handle_update_state(args):
    """
    Handle the update-state subcommand.
    
    Args:
        args: Parsed arguments from parse_args
    
    Returns:
        0 on success, 1 on failure
    """
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Updating state for task {args.task_id} with status {args.status}")
    
    try:
        # Load current state to ensure file exists and is valid
        state = load_state(Path(args.state_file))
        
        # Log task event
        if args.status == 'start':
            log_task_start(args.task_id, state)
        elif args.status == 'complete':
            log_task_complete(args.task_id, state)
        elif args.status == 'fail':
            # Mark as failed (using complete with failure flag)
            log_task_complete(args.task_id, state, success=False)
        
        # Save updated state
        save_state(state, Path(args.state_file))
        
        logger.info(f"State updated successfully for task {args.task_id}")
        return 0
        
    except (FileNotFoundError, ValidationError) as e:
        logger.error(f"Failed to update state: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error updating state: {e}")
        return 1


def handle_status(args):
    """
    Handle the status subcommand.
    
    Args:
        args: Parsed arguments from parse_args
    
    Returns:
        0 on success, 1 on failure
    """
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        state = load_state(Path(args.state_file))
        summary = get_state_summary(state)
        
        print("\n=== Project State Summary ===")
        print(f"Last Updated: {summary.get('last_updated', 'N/A')}")
        print(f"Current Task: {summary.get('current_task', 'N/A')}")
        print(f"Completed Tasks: {len(summary.get('completed_tasks', []))}")
        print(f"Failed Tasks: {len(summary.get('failed_tasks', []))}")
        
        if summary.get('last_task_hash'):
            print(f"Last Task Hash: {summary.get('last_task_hash')[:16]}...")
        
        print("===========================\n")
        return 0
        
    except FileNotFoundError:
        logger.error(f"State file not found: {args.state_file}")
        return 1
    except ValidationError as e:
        logger.error(f"Invalid state file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error reading state: {e}")
        return 1


def handle_reset_state(args):
    """
    Handle the reset-state subcommand.
    
    Args:
        args: Parsed arguments from parse_args
    
    Returns:
        0 on success, 1 on failure
    """
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not args.confirm:
        logger.warning("Reset requires confirmation. Use --confirm flag.")
        return 1
    
    try:
        reset_state(Path(args.state_file))
        logger.info(f"State reset successfully for file: {args.state_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to reset state: {e}")
        return 1


def main(args=None):
    """
    Main entry point for the CLI.
    
    Args:
        args: Optional list of arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parsed_args = parse_args(args)
    
    # Set random seed if provided
    if parsed_args.seed is not None:
        set_seed(parsed_args.seed)
    
    # Dispatch to appropriate handler
    if parsed_args.command == 'update-state':
        return handle_update_state(parsed_args)
    elif parsed_args.command == 'status':
        return handle_status(parsed_args)
    elif parsed_args.command == 'reset-state':
        return handle_reset_state(parsed_args)
    else:
        # No command provided, show help
        parsed_args.parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())