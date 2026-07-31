import sys
from code.config import get_config

def main():
    """Verify that all required config keys exist and are non-empty."""
    config = get_config()
    
    required_keys = [
        "W_LIST", "L_LIST", "NUM_REALIZATIONS", "SEED",
        "WEAK_DISORDER_CUTOFF", "NUMERICAL_RESIDUAL_THRESHOLD", "MAX_TM_ITERATIONS"
    ]
    
    missing = []
    empty = []
    
    for key in required_keys:
        if key not in config:
            missing.append(key)
        elif config[key] is None or config[key] == [] or config[key] == "":
            empty.append(key)
    
    if missing:
        print(f"ERROR: Missing required config keys: {missing}")
        return 1
    
    if empty:
        print(f"ERROR: Empty required config keys: {empty}")
        return 1
    
    print("SUCCESS: All required config keys are present and non-empty.")
    print(f"W_LIST: {config['W_LIST']}")
    print(f"L_LIST: {config['L_LIST']}")
    print(f"NUM_REALIZATIONS: {config['NUM_REALIZATIONS']}")
    print(f"SEED: {config['SEED']}")
    print(f"WEAK_DISORDER_CUTOFF: {config['WEAK_DISORDER_CUTOFF']}")
    print(f"NUMERICAL_RESIDUAL_THRESHOLD: {config['NUMERICAL_RESIDUAL_THRESHOLD']}")
    print(f"MAX_TM_ITERATIONS: {config['MAX_TM_ITERATIONS']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())