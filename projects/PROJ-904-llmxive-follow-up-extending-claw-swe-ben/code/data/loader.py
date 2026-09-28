import os
import re
import ast
import sys
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
from config import get_data_dir, get_output_dir, set_global_seeds

class ParsedIssue:
    def __init__(self, issue_description: str, repo_state: str):
        self.issue_description = issue_description
        self.repo_state = repo_state

class ClawSweBenchLoader:
    def __init__(self, data_dir: str, output_dir: str):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)

    def load_and_filter(self, filter_min_lines: int) -> List[ParsedIssue]:
        """Loads the dataset, filters instances with > filter_min_lines, and returns a list of ParsedIssue."""
        all_instances = []
        filtered_instances = []
        instance_count = 0

        # Simulate loading from a dataset for demonstration
        for i in range(100):  # Adjust the number of iterations based on the actual dataset size
            issue_description = f"This is a sample issue description {i}."
            repo_state = f"This is a sample repo state {i}."
            all_instances.append(ParsedIssue(issue_description, repo_state))

            # Count lines in the issue description as a proxy for file content length
            line_count = len(issue_description.splitlines())

            if line_count > filter_min_lines:
                filtered_instances.append(ParsedIssue(issue_description, repo_state))
                instance_count += 1
                self.logger.debug(f"Instance {i} added. Line count: {line_count}")
            else:
                self.logger.debug(f"Instance {i} filtered out. Line count: {line_count}")

        self.logger.info(f"Total instances: {len(all_instances)}")
        self.logger.info(f"Filtered instances: {instance_count}")
        return filtered_instances

def main():
    logging.basicConfig(level=logging.INFO)
    loader = ClawSweBenchLoader(data_dir="data/", output_dir="data/")
    filtered_instances = loader.load_and_filter(filter_min_lines=500)

    # Save the filtered instances to a file
    with open("data/filtered_swe_bench.parquet", "w") as f:
        for instance in filtered_instances:
            f.write(f"{instance.issue_description}\n")
    
    # Log the number of dropped instances and reasons
    
    
    
if __name__ == "__main__":
    main()