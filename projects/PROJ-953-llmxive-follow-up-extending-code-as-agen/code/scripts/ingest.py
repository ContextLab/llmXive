import os
import csv
import json
import hashlib
import sys
from pathlib import Path
from datasets import load_dataset
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_swe_bench(dataset_name, split='train', streaming=True):
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
        logging.info(f"Successfully loaded {dataset_name} dataset.")
        return dataset
    except Exception as e:
        logging.error(f"Failed to load {dataset_name} dataset: {e}")
        raise

def load_agent_bench(dataset_name, split='train', streaming=True):
    try:
        dataset = load_dataset(dataset_name, split=split, streaming=streaming)
        logging.info(f"Successfully loaded {dataset_name} dataset.")
        return dataset
    except Exception as e:
        logging.error(f"Failed to load {dataset_name} dataset: {e}")
        raise

def parse_swe_bench(example):
    try:
        task_id = example['task_id']
        code_diff = example['code_diff']
        original_code = example['original_code']
        return {'task_id': task_id, 'code_diff': code_diff, 'original_code': original_code, 'status': 'Parsed'}
    except Exception as e:
        logging.warning(f"Failed to parse SWE-Bench example: {e}")
        return {'task_id': example.get('task_id', 'unknown'), 'code_diff': None, 'original_code': None, 'status': 'Unparseable'}

def parse_agent_bench(example):
    try:
        task_id = example['task_id']
        code_diff = example['code_diff']
        original_code = example['original_code']
        return {'task_id': task_id, 'code_diff': code_diff, 'original_code': original_code, 'status': 'Parsed'}
    except Exception as e:
        logging.warning(f"Failed to parse AgentBench example: {e}")
        return {'task_id': example.get('task_id', 'unknown'), 'code_diff': None, 'original_code': None, 'status': 'Unparseable'}

def merge_datasets(swe_bench_dataset, agent_bench_dataset):
    merged_dataset = []
    for example in swe_bench_dataset:
        merged_dataset.append(example)
    for example in agent_bench_dataset:
        merged_dataset.append(example)
    return merged_dataset

def write_to_csv(data, filepath):
    try:
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['task_id', 'code_diff', 'original_code', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info(f"Successfully wrote data to CSV: {filepath}")
    except Exception as e:
        logging.error(f"Failed to write data to CSV: {e}")
        raise

def write_to_json(data, filepath):
    try:
        with open(filepath, 'w') as jsonfile:
            json.dump(data, jsonfile)
        logging.info(f"Successfully wrote data to JSON: {filepath}")
    except Exception as e:
        logging.error(f"Failed to write data to JSON: {e}")
        raise

def main():
    swe_bench_dataset = load_swe_bench('swebench/agent_bench_eval', streaming=True)
    agent_bench_dataset = load_agent_bench('swebench/agent_bench_eval', streaming=True)

    swe_bench_parsed = list(map(parse_swe_bench, swe_bench_dataset))
    agent_bench_parsed = list(map(parse_agent_bench, agent_bench_dataset))

    merged_dataset = merge_datasets(swe_bench_parsed, agent_bench_parsed)

    # Limit to N=500 or fewer tasks for RAM constraint
    N = 500
    limited_dataset = merged_dataset[:N]

    data_filepath = Path('data/raw/swe_bench_agentbench_subset.csv')
    json_filepath = Path('data/logs/ingest_sample_log.json')

    write_to_csv(limited_dataset, data_filepath)

    log_data = {'sample_size': len(limited_dataset),
                'dataset_size': len(merged_dataset),
                'ram_limit_reached': len(limited_dataset) < len(merged_dataset)}

    write_to_json(log_data, json_filepath)

if __name__ == "__main__":
    main()