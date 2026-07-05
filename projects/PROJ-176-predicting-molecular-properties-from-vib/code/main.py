import argparse
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.download import main as download_main
from data.preprocess import main as preprocess_main
from models.trainer import main as train_main
from utils.seed_utils import set_seed
from utils.timeout_wrapper import enforce_timeout
from utils.update_state import update_task_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

def cmd_download(args):
    """Download QM9 and IR-spectra datasets."""
    logger.info("Starting data download...")
    set_seed(args.seed)
    download_main()
    logger.info("Data download completed.")

def cmd_preprocess(args):
    """Preprocess aligned datasets."""
    logger.info("Starting data preprocessing...")
    set_seed(args.seed)
    
    def _run_preprocess():
        preprocess_main()
    
    if args.timeout:
        enforce_timeout(_run_preprocess, args.timeout)
    else:
        _run_preprocess()
        
    logger.info("Data preprocessing completed.")

def cmd_train(args):
    """Train the 1-D CNN model with timeout enforcement."""
    logger.info("Starting model training...")
    set_seed(args.seed)
    
    def _run_training():
        train_main(
            data_path=args.data_path,
            output_dir=args.output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            patience=args.patience,
            log_dir=args.log_dir
        )
    
    # Enforce timeout if specified using the timeout wrapper
    if args.timeout:
        logger.info(f"Training will be enforced with a timeout of {args.timeout} seconds.")
        enforce_timeout(_run_training, args.timeout)
    else:
        logger.info("No timeout specified for training.")
        _run_training()
        
    logger.info("Model training completed.")
    
    # Update state for task completion
    state_path = project_root / "state" / "training_state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    update_task_state("T024", "completed", str(state_path))

def main():
    parser = argparse.ArgumentParser(
        description="Molecular Property Prediction Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download datasets")
    download_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    download_parser.set_defaults(func=cmd_download)

    # Preprocess command
    preprocess_parser = subparsers.add_parser("preprocess", help="Preprocess data")
    preprocess_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    preprocess_parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    preprocess_parser.set_defaults(func=cmd_preprocess)

    # Train command
    train_parser = subparsers.add_parser("train", help="Train the model")
    train_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    train_parser.add_argument("--data-path", type=str, default="data/preprocessed/aligned_data.npz", 
                            help="Path to preprocessed .npz file")
    train_parser.add_argument("--output-dir", type=str, default="results/models", 
                            help="Directory to save model checkpoints")
    train_parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    train_parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    train_parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    train_parser.add_argument("--patience", type=int, default=10, help="Early stopping patience")
    train_parser.add_argument("--log-dir", type=str, default="runs/training", 
                            help="TensorBoard log directory")
    train_parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    train_parser.set_defaults(func=cmd_train)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()