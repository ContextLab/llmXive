"""
delete_task_marker.py

Removes the T041 task marker from tasks.md, as the task has been
identified as DELETED and its functionality subsumed by T022a/T022b.
"""
import logging
from pathlib import Path

def main():
    """
    Removes the T041 line from tasks.md.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Determine project root relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    tasks_file = project_root / "tasks.md"

    if not tasks_file.exists():
        logger.error(f"File not found: {tasks_file}")
        return 1

    logger.info(f"Processing {tasks_file}...")

    try:
        content = tasks_file.read_text(encoding='utf-8')
        lines = content.splitlines()

        # Identify the line to remove
        # The line is: "- [ ] T041 (DELETED - Contradictory approximation logic removed; Per-sample approach in T022a/T022b is correct). <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->"
        target_marker = "T041"
        
        new_lines = []
        removed = False
        for line in lines:
            # Check if the line contains the T041 marker
            if target_marker in line and line.strip().startswith("- [") and "DELETED" in line:
                logger.info(f"Removing T041 marker: {line.strip()}")
                removed = True
                continue
            new_lines.append(line)

        if removed:
            new_content = "\n".join(new_lines)
            tasks_file.write_text(new_content, encoding='utf-8')
            logger.info("Successfully removed T041 task marker.")
        else:
            logger.warning("T041 task marker not found. It may have already been removed.")

        return 0

    except Exception as e:
        logger.error(f"Error processing tasks.md: {e}")
        return 1

if __name__ == "__main__":
    exit(main())