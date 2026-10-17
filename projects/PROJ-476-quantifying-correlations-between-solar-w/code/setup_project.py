import pathlib
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def setup():
    dirs = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/tests",
        "data/raw",
        "data/processed",
        "results",
        "figures",
    ]
    for d in dirs:
        p = pathlib.Path(d)
        p.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {d}")

if __name__ == "__main__":
    setup()
