"""Visualization script."""
import argparse
import matplotlib.pyplot as plt
import pandas as pd
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    input_path = paths.path(args.input)
    if not input_path.is_file():
        log.warning("Input CSV %s not found.", input_path)
        return

    df = pd.read_csv(input_path)
    plt.figure(figsize=(8, 5))
    for src in df["source_type"].unique():
        sub = df[df["source_type"] == src].sort_values("complexity_level")
        plt.plot(sub["complexity_level"], sub["latency_ms"], marker="o", label=src)
    plt.title("Latency vs. Complexity")
    plt.xlabel("Complexity Level")
    plt.ylabel("Latency (ms)")
    plt.legend()
    plt.grid(True)

    out_path = paths.path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    log.info("Plot saved to %s", out_path)

if __name__ == "__main__":
    main()
