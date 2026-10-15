"""
Simple verification script for the project configuration.
It checks that:
  * L_LIST contains the required large‑system size 1600,
  * NUM_REALIZATIONS equals 100,
  * W_LIST contains exactly ten disorder widths and includes 0.5, 1.0, and 2.0.
The script exits with status 0 on success and prints a short summary.
"""
import sys
from code.config import get_config

def main() -> None:
    cfg = get_config()

    # Check L_LIST
    if 1600 not in cfg.get("L_LIST", []):
        sys.exit("ERROR: L_LIST does not contain 1600")

    # Check NUM_REALIZATIONS
    if cfg.get("NUM_REALIZATIONS") != 100:
        sys.exit(f"ERROR: NUM_REALIZATIONS is {cfg.get('NUM_REALIZATIONS')}, expected 100")

    # Check W_LIST length and required entries
    w_list = cfg.get("W_LIST", [])
    required = {0.5, 1.0, 2.0}
    if len(w_list) != 10 or not required.issubset(set(w_list)):
        sys.exit(f"ERROR: W_LIST must have 10 entries and include {required}")

    print("Configuration verification passed.")
    # Optionally, write a tiny JSON flag for downstream scripts
    import json
    from pathlib import Path
    flag_path = Path("data/metadata") / "config_verified.json"
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text(json.dumps({"verified": True}))

if __name__ == "__main__":
    main()