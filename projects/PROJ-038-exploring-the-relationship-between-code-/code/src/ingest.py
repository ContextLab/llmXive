import os
import subprocess
import sys
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

def DataFetchError(message):
    raise Exception(f"Data Fetch Error: {message}")

def get_defects4j_path():
    try:
        return os.environ["DEFECTS4J_HOME"]
    except KeyError:
        raise ValueError("DEFECTS4J_HOME environment variable not set.")

def run_defects4j_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise DataFetchError(f"Defects4J command failed: {e.stderr}")

def list_available_projects():
    command = [get_defects4j_path(), "list"]
    output = run_defects4j_command(command)
    return [line.split()[0] for line in output.splitlines()]

def get_project_size(project_id):
    try:
       command = [get_defects4j_path(), "info", project_id]
       output = run_defects4j_command(command)
       # Extract the number of files from the output. This is a brittle approach, and might need adjusting.
       lines = output.splitlines()
       for line in lines:
           if "Number of files" in line:
               return int(line.split(":")[1].strip())
       return 0
    except Exception as e:
        logging.error(f"Error getting project size for {project_id}: {e}")
        return 0

def get_current_memory_usage_bytes():
  import psutil
  process = psutil.Process(os.getpid())
  return process.memory_info().rss

def validate_ram_limit(max_ram_bytes):
    if get_current_memory_usage_bytes() > max_ram_bytes:
        raise ValueError(f"RAM usage exceeds limit ({max_ram_bytes} bytes).")

def is_generated_or_non_java(file_path):
  return ".class" in file_path or not file_path.endswith(".java")


def filter_java_files(project_dir, files):
    return [f for f in files if f.endswith(".java")]

def select_dynamic_subset(projects, max_files=10000, max_ram_bytes = 6 * 1024 * 1024 * 1024): # 6GB default
    selected_projects = []
    total_files = 0
    for project in projects:
        project_dir = Path(f"defects4j/projects/{project}")
        if not project_dir.exists():
            logging.warning(f"Project directory {project_dir} does not exist.")
            continue

        num_files = get_project_size(project)
        if num_files == 0:
          continue

        if total_files + num_files <= max_files:
            selected_projects.append(project)
            total_files += num_files
            logging.info(f"Added project {project}, current file count: {total_files}")
        else:
            break

    return selected_projects


def download_defects4j_subset(projects):
  for project in projects:
      command = [get_defects4j_path(), "checkout", project]
      run_defects4j_command(command)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        projects = list_available_projects()
        selected_projects = select_dynamic_subset(projects)
        download_defects4j_subset(selected_projects)

        logging.info(f"Downloaded projects: {selected_projects}")

    except Exception as e:
        logging.error(f"Error during ingestion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()