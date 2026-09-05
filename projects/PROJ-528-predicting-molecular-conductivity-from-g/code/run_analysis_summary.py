import os
import sys
import logging
from code.logging_config import setup_logging
from code.analysis_summary import main

def main_run():
    setup_logging()
    main()

if __name__ == '__main__':
    main_run()
