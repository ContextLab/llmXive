"""
Runner for the complexity‑visualization examples (Task T068).

The heavy lifting lives in ``analysis.complexity_visualization``.  This
thin wrapper simply invokes its ``main`` function, which is expected to
generate the figure ``data/plots/complexity_visualization_examples.png``.
"""

from analysis.complexity_visualization import main as viz_main


def main() -> None:
    """Execute the visualization pipeline."""
    viz_main()


if __name__ == "__main__":
    main()