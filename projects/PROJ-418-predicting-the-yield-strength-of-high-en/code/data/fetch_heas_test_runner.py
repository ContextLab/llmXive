"""
Helper script used by the evaluation harness to run the fetch_heas
module and ensure that the required CSV file is produced.
"""
from data.fetch_heas import fetch_heas

if __name__ == "__main__":
    fetch_heas()