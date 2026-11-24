"""Entry‑point script to generate the synthetic query dataset.

The script is invoked by the task runner to ensure that
``data/processed/generation_log.json`` exists before the unit tests are
executed.
"""
from llmxive_toolkit import paths
from generators.synthetic_query import SyntheticQueryGenerator

def main() -> None:
    generator = SyntheticQueryGenerator()
    out_path = paths.data("processed", "generation_log.json")
    generator.save_queries(out_path, count=500)

if __name__ == "__main__":
    main()
