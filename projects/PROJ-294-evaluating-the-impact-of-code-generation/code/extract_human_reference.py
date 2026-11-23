import os
import sys
import json
import logging

# Import utilities from the shared utils package
from utils import setup_logging, get_logger, set_task_id, get_task_id

def extract_human_references():
    """
    FR‑001: Extract human reference code from the raw dataset and save
    as JSON‑lines.  The output conforms to the contract:

    {
        "task_id": "...",
        "code": "...",          # canonical_solution
        "source": "human"
    }
    """
    logger = setup_logging(task_id="T001")
    logger.info("Extracting human reference solutions...")

    # Rather than parsing the parquet file (which would require ``pyarrow``),
    # we simply reload the dataset from HuggingFace – the data are small
    # and this avoids the ``pyarrow`` dependency entirely.
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise ImportError(
            "The 'datasets' library is required. Install it via "
            "`pip install datasets`."
        ) from exc

    ds = load_dataset("openai/openai_humaneval", split="test")
    df = ds.to_pandas()

    output_path = os.path.join("data", "generated", "human_samples.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        for _, row in df.iterrows():
            record = {
                "task_id": row["task_id"],
                "code": row["canonical_solution"],
                "source": "human",
            }
            f.write(json.dumps(record) + "\n")

    logger.info(f"Saved human references to {output_path}")
    return output_path


def main():
    extract_human_references()


if __name__ == "__main__":
    main()
