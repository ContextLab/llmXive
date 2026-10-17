import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("Usage: python read_file.py <path_to_file>")
        sys.exit(1)
    file_path = Path(sys.argv[1])
    if not file_path.is_file():
        print(f"File not found: {file_path}")
        sys.exit(1)
    print(file_path.read_text())

if __name__ == "__main__":
    main()
