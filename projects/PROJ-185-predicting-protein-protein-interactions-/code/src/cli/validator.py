import argparse


def validate_threshold(args: argparse.Namespace) -> None:
    """
    Ensure that the '--threshold' argument is at least 0.75.

    Raises
    ------
    argparse.ArgumentError
        If the threshold is below the required minimum.
    """
    # If the attribute is missing, nothing to validate.
    if not hasattr(args, "threshold"):
        return
    threshold = args.threshold
    if threshold < 0.75:
        raise argparse.ArgumentError(
            None,
            f"--threshold must be >= 0.75 (got {threshold})",
        )
