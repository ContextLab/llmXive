"""Visualization script.

Generates a simple interaction plot (latency vs. complexity) for each
source type and saves it as a PNG file.
"""

import argparse
import matplotlib.pyplot as plt
import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(description="Create interaction plot.")
    parser.add_argument("--input", required=True, help="Path to execution_logs CSV.")
    parser.add_argument("--output", required=True, help="Path for the PNG output.")
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    plt.figure(figsize=(8, 5))
    for src in df["source_type"].unique():
        sub = df[df["source_type"] == src]
        # Sort by complexity for a clean line plot
        sub = sub.sort_values("complexity_level")
        plt.plot(
            sub["complexity_level"],
            sub["latency_ms"],
            marker="o",
            label=src,
        )
    plt.title("Latency vs. Complexity by Source Type")
    plt.xlabel("Complexity Level")
    plt.ylabel("Latency (ms)")
    plt.legend()
    plt.grid(True)

    out_path = paths.path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    log.info("Interaction plot saved to %s", out_path)

if __name__ == "__main__":
    main()
