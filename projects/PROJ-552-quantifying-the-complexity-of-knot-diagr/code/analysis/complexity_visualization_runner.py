"""
Runner that generates the complexity‑visualisation examples plot.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

from reproducibility.logs import get_logger, log_operation
from analysis.complexity_visualization import (
    KnotRecord,
    generate_complexity_visualization_examples,
)


@log_operation("generate_complexity_visualization_examples", output_path_arg="output_path")
def main(output_path: Path = Path("data/plots/complexity_visualization_examples.png")) -> None:
    """
    Produce a small set of example visualisations that illustrate how the
    complexity metric (crossing number + braid index) behaves for a few
    representative knots.
    """
    logger = get_logger()
    logger.log("generate_complexity_visualization_examples", "start")

    # Load a tiny subset of the cleaned data – the function itself knows how
    # to pick representative knots.
    df = pd.read_csv(Path("data/processed/knots_cleaned.csv"))
    records = [
        KnotRecord(
            name=row["name"],
            crossing_number=int(row["crossing_number"]),
            braid_index=int(row["braid_index"]),
            volume=float(row["volume"]) if "volume" in row and not pd.isna(row["volume"]) else None,
        )
        for _, row in df.head(20).iterrows()
    ]

    fig = generate_complexity_visualization_examples(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    logger.log(
        "generate_complexity_visualization_examples",
        "end_success",
        details={"output": str(output_path)},
    )


if __name__ == "__main__":
    main()
