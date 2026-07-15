import sys

REQUIRED_PACKAGES = [
    "pandas",
    "scipy",
    "statsmodels",
    "numpy",
    "requests",
    "yaml",
    "jsonschema",
    "vaderSentiment",
]

def main():
    failed = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            print(f"OK: {package}")
        except ImportError as e:
            failed.append(package)
            print(f"FAIL: {package} - {e}")

    if failed:
        print(f"\nMissing packages: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nAll required packages imported successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
