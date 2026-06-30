"""
Base CLI entry point for the Qwen-VLA Cross-Embodiment Transfer Study.

Implements the argument parser using `click` with support for the `--ratio`
argument as specified in T005. Aggregation logic and CSV generation are
deferred to T025/T027.
"""
import click
import os
import sys

# Ensure the project root is in the path if running as a script
# This allows imports from 'src' modules if the project is installed or run correctly
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@click.group()
@click.version_option(version="0.1.0", prog_name="qwen-vla-cli")
def cli():
    """
    Qwen-VLA Cross-Embodiment Transfer Study CLI.

    This tool orchestrates data loading, training, evaluation, and statistical
    analysis for the cross-embodiment transfer study.
    """
    pass


@cli.command()
@click.option(
    "--ratio",
    type=float,
    default=1.0,
    help="Data composition ratio for the experiment (0.0 to 1.0). "
         "Used for ablation studies (T025/T027).",
    show_default=True
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False, dir_okay=True),
    default="data",
    help="Directory for output artifacts (checkpoints, logs, results).",
    show_default=True
)
def run(ratio: float, output_dir: str):
    """
    Execute the main pipeline with the specified data ratio.

    Note: This command currently validates the arguments and prints the configuration.
    The actual training, evaluation, and aggregation logic (FR-006) are implemented
    in T015, T016, T025, and T027.
    """
    # Validate ratio
    if not (0.0 <= ratio <= 1.0):
        raise click.BadParameter("Ratio must be between 0.0 and 1.0.")

    # Validate output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        click.echo(f"Created output directory: {output_dir}")

    click.echo(f"Configuration loaded:")
    click.echo(f"  - Data Ratio: {ratio}")
    click.echo(f"  - Output Directory: {output_dir}")
    click.echo(f"  - Status: Ready to run (Aggregation logic deferred to T025/T027)")

    # Placeholder for future aggregation logic
    # TODO: Integrate ablation_runner.py and stat_utils.py here in T025/T027
    # For now, we simply acknowledge the arguments.
    click.echo("CLI arguments parsed successfully.")


@cli.command()
def version():
    """Print the version of the CLI tool."""
    click.echo("Qwen-VLA Cross-Embodiment CLI v0.1.0")


if __name__ == "__main__":
    cli()
