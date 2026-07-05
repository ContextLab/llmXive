import os
import sys

def main():
    dirs = [
        "data/raw",
        "data/generated",
        "data/analysis",
        "results/figures",
        "state"
    ]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

if __name__ == "__main__":
    main()
