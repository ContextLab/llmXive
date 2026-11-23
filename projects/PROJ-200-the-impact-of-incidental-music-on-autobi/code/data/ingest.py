"""
Thin wrapper that forwards to the full ingestion implementation.
"""
from data_ingestion import main as ingest_main

def main():
    ingest_main()

if __name__ == "__main__":
    main()
