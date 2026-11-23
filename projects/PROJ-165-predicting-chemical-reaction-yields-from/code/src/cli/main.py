import argparse
import sys
import logging
from pathlib import Path
from src.utils.state_manager import update_state, load_state, log_task_start, log_task_complete, reset_state
from src.utils.seeds import set_seed

def parse_args(args=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CLI entry point for the llmXive chemical reaction yield prediction pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # --update-state flag (global option for backward compatibility or specific usage)
    parser.add_argument(
        "--update-state",
        action="store_true",
        help="Update the project state hash and timestamp based on current file system changes.",
    )
    
    # Subcommand: update-state
    parser_update = subparsers.add_parser("update-state", help="Update project state metadata")
    parser_update.add_argument(
        "--task-id",
        type=str,
        default=None,
        help="Optional task ID to log state update for.",
    )
    parser_update.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without actually writing changes.",
    )
    
    # Subcommand: status
    parser_status = subparsers.add_parser("status", help="Display current project state summary")
    parser_status.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed state history.",
    )
    
    # Subcommand: reset-state
    parser_reset = subparsers.add_parser("reset-state", help="Reset project state to initial values")
    parser_reset.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm reset action (required to prevent accidental data loss).",
    )
    
    # Subcommand: train (placeholder for future implementation)
    parser_train = subparsers.add_parser("train", help="Train the attention model")
    parser_train.add_argument(
        "--config",
        type=str,
        default="src/config/defaults.yaml",
        help="Path to configuration file.",
    )
    
    # Subcommand: eval (placeholder for future implementation)
    parser_eval = subparsers.add_parser("eval", help="Evaluate the trained model")
    parser_eval.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the trained model weights.",
    )
    
    # Global seed option
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Set random seed for reproducibility.",
    )
    
    # Logging options
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level.",
    )
    
    parsed_args = parser.parse_args(args)
    return parsed_args

def handle_update_state(args, project_root: Path):
    """Handle the --update-state flag or update-state subcommand."""
    task_id = getattr(args, 'task_id', None)
    dry_run = getattr(args, 'dry_run', False)
    
    logging.info(f"Updating project state (task_id={task_id}, dry_run={dry_run})")
    
    if task_id:
        log_task_start(task_id)
    
    if dry_run:
        summary = load_state(project_root)
        logging.info(f"[DRY RUN] Current state summary: {summary}")
    else:
        success = update_state(project_root, task_id=task_id)
        if success:
            logging.info("Project state updated successfully.")
        else:
            logging.error("Failed to update project state.")
            return False
    
    if task_id:
        log_task_complete(task_id)
    
    return True

def handle_status(args, project_root: Path):
    """Handle the status subcommand."""
    verbose = getattr(args, 'verbose', False)
    state = load_state(project_root)
    
    if not state:
        logging.warning("No state file found. The project may not be initialized.")
        return True
    
    logging.info("=== Project State Summary ===")
    logging.info(f"Last Updated: {state.get('timestamp', 'N/A')}")
    logging.info(f"State Hash: {state.get('hash', 'N/A')}")
    logging.info(f"Completed Tasks: {len(state.get('completed_tasks', []))}")
    
    if verbose:
        logging.info("\n--- Task History ---")
        history = state.get('task_history', [])
        for entry in history[-10:]:  # Show last 10 entries
            logging.info(f"  {entry.get('timestamp', 'N/A')} | {entry.get('task_id', 'N/A')} | {entry.get('status', 'N/A')}")
    
    return True

def handle_reset_state(args, project_root: Path):
    """Handle the reset-state subcommand."""
    confirm = getattr(args, 'confirm', False)
    
    if not confirm:
        logging.error("Reset requires confirmation. Use --confirm flag.")
        return False
    
    logging.warning("Resetting project state...")
    success = reset_state(project_root)
    
    if success:
        logging.info("Project state reset successfully.")
    else:
        logging.error("Failed to reset project state.")
    
    return success

def handle_train(args, project_root: Path):
    """Placeholder for train subcommand."""
    logging.info("Train subcommand triggered. Implementation pending in T027.")
    return True

def handle_eval(args, project_root: Path):
    """Placeholder for eval subcommand."""
    logging.info("Eval subcommand triggered. Implementation pending in T036.")
    return True

def main(args=None):
    """Main entry point for the CLI."""
    parsed_args = parse_args(args)
    
    # Setup logging
    log_level = getattr(parsed_args, 'log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    
    # Set seed if provided
    if hasattr(parsed_args, 'seed') and parsed_args.seed is not None:
        set_seed(parsed_args.seed)
        logging.info(f"Random seed set to {parsed_args.seed}")
    
    # Determine project root (assume current directory or parent of src)
    current_path = Path.cwd()
    if (current_path / "src").exists():
        project_root = current_path
    else:
        # Fallback: look for src in parent
        parent = current_path.parent
        if (parent / "src").exists():
            project_root = parent
        else:
            logging.error("Could not determine project root. Ensure 'src/' directory exists.")
            sys.exit(1)
    
    # Handle --update-state flag (legacy/global)
    if getattr(parsed_args, 'update_state', False):
        # Convert to subcommand-like behavior
        class FakeArgs:
            task_id = None
            dry_run = False
        return handle_update_state(FakeArgs(), project_root)
    
    # Handle subcommands
    if parsed_args.command == "update-state":
        return handle_update_state(parsed_args, project_root)
    elif parsed_args.command == "status":
        return handle_status(parsed_args, project_root)
    elif parsed_args.command == "reset-state":
        return handle_reset_state(parsed_args, project_root)
    elif parsed_args.command == "train":
        return handle_train(parsed_args, project_root)
    elif parsed_args.command == "eval":
        return handle_eval(parsed_args, project_root)
    else:
        # No command provided, show help
        parsed_args = parse_args(["--help"])
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)