import json
from pathlib import Path
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("power_limitation")

def generate_limitation_report():
    """
    Generates a report on power limitations if full run was blocked.
    """
    pass

def main():
    generate_limitation_report()

if __name__ == "__main__":
    main()
