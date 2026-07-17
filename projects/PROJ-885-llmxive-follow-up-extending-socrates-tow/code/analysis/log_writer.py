import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import ensure_directories

logger = logging.getLogger(__name__)

def write_experiment_logs(
    logs: List[Dict[str, Any]], output_path: Optional[Path] = None
) -> Path:
    """
    Write experiment logs to a JSON file.

    Args:
        logs: List of log dictionaries containing trajectory ID, condition,
              injected state, and LLM output.
        output_path: Optional path to write to. Defaults to data/processed/experiment_logs.json.

    Returns:
        The path where the logs were written.
    """
    if output_path is None:
        output_path = Path("data/processed/experiment_logs.json")

    ensure_directories(output_path)

    timestamp = datetime.now().isoformat()
    record = {
        "metadata": {
            "generated_at": timestamp,
            "total_entries": len(logs),
        },
        "logs": logs,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    logger.info(f"Wrote {len(logs)} experiment logs to {output_path}")
    return output_path

def load_experiment_logs(path: Path) -> List[Dict[str, Any]]:
    """
    Load experiment logs from a JSON file.

    Args:
        path: Path to the logs file.

    Returns:
        List of log dictionaries.
    """
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("logs", [])

def main() -> None:
    """
    Example usage: Write a dummy log to verify the writer works.
    """
    logging.basicConfig(level=logging.INFO)
    dummy_log = {
        "trajectory_id": "test-001",
        "condition": "Adapter",
        "injected_state": "de-escalate",
        "llm_output": "This is a test output.",
        "timestamp": datetime.now().isoformat(),
    }
    write_experiment_logs([dummy_log])
    logger.info("Dummy log written successfully.")

if __name__ == "__main__":
    main()