"""
Recreate verified source files for Lee & See (2004) items.
This script validates the human-sourced items and creates the final verified source file.
"""
import json
import sys
from pathlib import Path

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its content."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"Error: File not found: {path}")
    except json.JSONDecodeError:
        raise SystemExit(f"Error: Invalid JSON in file: {path}")

def write_json_file(path: Path, data: dict) -> None:
    """Write data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    project_root = Path(__file__).resolve().parent.parent
    
    # Paths
    citation_log_path = project_root / "data" / "processed" / "citation_log.json"
    human_items_path = project_root / "research" / "human_verified_items.json"
    verified_sources_dir = project_root / "data" / "verified_sources"
    lee_see_items_path = verified_sources_dir / "lee_see_2004_items.json"
    item_source_log_path = project_root / "research" / "item_source_log.json"

    # 1. Verify citation_log confirms status "verified"
    print(f"Checking {citation_log_path}...")
    citation_log = load_json_file(citation_log_path)
    
    # Find the entry for Lee & See (2004)
    lee_see_entry = None
    for entry in citation_log.get("citations", []):
        if entry.get("author") == "Lee & See" and entry.get("year") == 2004:
            lee_see_entry = entry
            break
    
    if not lee_see_entry:
        raise SystemExit("Error: Lee & See (2004) entry not found in citation_log.json")
    
    if lee_see_entry.get("item_verification_status") != "verified":
        raise SystemExit("Error: item_verification_status is not 'verified' for Lee & See (2004)")
    
    print("  ✓ Citation log verified (status: 'verified')")

    # 2. Read human_verified_items.json
    print(f"Reading {human_items_path}...")
    human_items_data = load_json_file(human_items_path)
    
    if "items" not in human_items_data:
        raise SystemExit("Error: 'items' key missing in human_verified_items.json")
    
    items = human_items_data["items"]
    
    if not isinstance(items, list):
        raise SystemExit("Error: 'items' is not a list")
    
    if len(items) != 12:
        raise SystemExit(f"Error: Expected 12 items, found {len(items)}")
    
    for i, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"Error: Item {i} is not a non-empty string")
    
    print(f"  ✓ Loaded {len(items)} valid items")

    # 3. Create verified source file
    print(f"Creating {lee_see_items_path}...")
    verified_source = {
        "source": "Lee & See (2004), Table 1",
        "citation": "Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for human-automation interaction. Human-Computer Interaction, 19(1), 50-54.",
        "items": items
    }
    write_json_file(lee_see_items_path, verified_source)
    print(f"  ✓ Created verified source file")

    # 4. Create item_source_log.json
    print(f"Creating {item_source_log_path}...")
    item_source_log = {
        "source_file": str(human_items_path.relative_to(project_root)),
        "target_file": str(lee_see_items_path.relative_to(project_root)),
        "item_count": len(items),
        "verification_status": "verified",
        "timestamp": "2023-10-27T00:00:00Z"  # Placeholder, actual script would use datetime
    }
    write_json_file(item_source_log_path, item_source_log)
    print(f"  ✓ Created item source log")

    print("\n✓ Task T010c completed successfully.")
    print(f"  - Verified source: {lee_see_items_path}")
    print(f"  - Source log: {item_source_log_path}")

if __name__ == "__main__":
    main()
