"""
CLI entry point for the Qwen-VLA Cross-Embodiment Transfer Study.

This module implements the base CLI using `click`. It currently supports
the `--ratio` argument for data composition ablation studies (FR-006),
though the full aggregation and CSV generation logic is deferred to
T025/T027.
"""

import click
import os
import sys

# Ensure the project root is in the path if running directly
# This allows imports like `from src.data.dataset_loader import ...`
# when the script is invoked as `python src/cli.py`
if __name__ == "__main__":
    # Add the parent directory to sys.path to resolve 'src' imports
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

@click.group()
@click.version_option(version="0.1.0", prog_name="qwen-vla-cli")
def cli():
    """
    Qwen-VLA Cross-Embodiment Transfer Study CLI.

    Main entry point for training, evaluation, and ablation studies.
    """
    pass


@cli.command()
@click.option(
    "--ratio",
    type=float,
    default=1.0,
    help="Data composition ratio for ablation study (0.0, 0.5, 1.0). "
         "Used to filter the dataset size before training.",
    show_default=True
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to a JSON/YAML configuration file (future use)."
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate arguments and configuration without executing the full pipeline."
)
def train(ratio, config, dry_run):
    """
    Start the training pipeline.

    This command accepts the `--ratio` argument to determine the proportion
    of the dataset to use. The actual training loop and dataset filtering
    logic are implemented in `src/training/train_loop.py` and
    `src/data/dataset_loader.py`.

    Example:
      python -m src.cli train --ratio 0.5
    """
    click.echo(f"Training command invoked with ratio={ratio}")

    if dry_run:
        click.echo("Dry-run mode: Validating arguments only.")
        if not (0.0 <= ratio <= 1.0):
            click.echo("Error: Ratio must be between 0.0 and 1.0.")
            sys.exit(1)
        click.echo("Validation successful.")
        return

    # Placeholder for the actual training execution.
    # The real implementation will call src.training.train_loop.main(ratio=ratio)
    # when T015 is implemented.
    click.echo(f"Starting training with data ratio: {ratio}")
    # In a real run, this would be:
    # from src.training import train_loop
    # train_loop.main(ratio=ratio)
    click.echo("Training simulation complete (implementation deferred to T015).")


@cli.command()
@click.option(
    "--ratio",
    type=float,
    default=1.0,
    help="Data composition ratio for evaluation (matches training ratio).",
    show_default=True
)
def evaluate(ratio):
    """
    Run zero-shot evaluation on the trained model.

    Requires a trained checkpoint. The evaluation logic is implemented
    in `src/evaluation/libero_eval.py`.
    """
    click.echo(f"Evaluation command invoked with ratio={ratio}")
    # Placeholder for T016 implementation
    click.echo("Evaluation simulation complete (implementation deferred to T016).")


@cli.command()
def stats():
    """
    Run statistical significance tests (Wilcoxon signed-rank).

    Executes the comparison between cross-embodiment and baseline results.
    Logic is implemented in `src/statistics/wilcoxon_test.py`.
    """
    click.echo("Running statistical analysis...")
    # Placeholder for T021 implementation
    click.echo("Statistical analysis simulation complete (implementation deferred to T021).")


if __name__ == "__main__":
    cli()