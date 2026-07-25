import csv
import json
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path
import tracemalloc

def load_videokr_dataset(data_dir):
    """Loads the VideoKR dataset."""
    filepath = os.path.join(data_dir, "videokr_sft.csv")
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    return data

def load_graph(data_dir):
    """Loads the Knowledge Graph."""
    filepath = os.path.join(data_dir, "knowledge_graph.json")
    with open(filepath, "r") as f:
        graph = json.load(f)
    return graph

def map_entities_to_nodes(question, graph):
    """Maps entities in the question to nodes in the graph."""
    # Placeholder for entity linking logic
    # Replace with actual implementation using fuzzy matching or embedding similarity
    logging.info("Mapping entities...")
    entity_node_id = "unknown"
    confidence = 0.0

    if "Paris" in question:
        entity_node_id = "Paris"
        confidence = 0.9
    elif "Leonardo da Vinci" in question:
        entity_node_id = "Leonardo da Vinci"
        confidence = 0.9

    return entity_node_id, confidence

def calculate_chain_length(graph, start_node, end_node):
    """Calculates the shortest path between two nodes in the graph."""
    # Placeholder for BFS implementation
    # Replace with actual implementation using Breadth-First Search
    logging.info("Calculating chain length...")
    if start_node == end_node:
        return 0

    # Simplified example - assumes direct connection or no path
    if start_node in graph and end_node in graph:
      return 1 # Assume a single hop if node exists
    else:
      return float('inf')  # Infinite distance if nodes do not exist


def bin_hop_length(chain_length):
    """Bins the chain length into categories (1, 2, 3+)."""
    if chain_length == 1:
        return "1"
    elif chain_length == 2:
        return "2"
    else:
        return "3+"

def run_pilot_sample(data):
  logging.info("Running pilot sample...")
  pilot_size = min(10, len(data)) #ensure not larger than data size
  pilot_data = data[:pilot_size]
  return pilot_data

def oversample_dataset(data):
    #Placeholder for oversampling if needed. Currently returns original data.
    logging.info("Oversampling dataset (placeholder)...")
    return data

def process_chunk(chunk, graph):
    """Processes a chunk of the dataset."""
    processed_records = []
    for record in chunk:
        question = record["question"]
        entity_node_id, confidence = map_entities_to_nodes(question, graph)

        if confidence > 0.5:  # Threshold for mapping
            chain_length = calculate_chain_length(graph, entity_node_id, "answer")
            chain_bin = bin_hop_length(chain_length)
            processed_record = {
                "id": record["id"],
                "question": question,
                "answer": record["answer"],
                "chain_length": int(chain_length),
                "chain_bin": chain_bin,
                "correctness": "unknown",  # Placeholder for correctness
            }
            processed_records.append(processed_record)
        else:
            logging.warning(f"Skipping question due to low confidence: {question}")
    return processed_records

def main():
    """Main function to annotate the graph."""
    data_dir = os.path.join(".", "data", "raw")
    graph = load_graph(data_dir)
    dataset = load_videokr_dataset(data_dir)

    #Chunk processing with pilot sample for demonstration
    chunk_size = 10 #process in chunks of 10 records.
    pilot_sample = run_pilot_sample(dataset)
    processed_records = []


    for i in range(0, len(pilot_sample), chunk_size):
      chunk = pilot_sample[i:i+chunk_size]
      processed_records.extend(process_chunk(chunk, graph))

    output_file = os.path.join(".", "data", "processed", "annotated_videokr.csv")
    with open(output_file, "w", newline="") as csvfile:
        fieldnames = ["id", "question", "answer", "chain_length", "chain_bin", "correctness"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_records)

    logging.info(f"Annotated data written to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tracemalloc.start() #Start memory tracking
    main()
    tracemalloc.stop() #Stop memory tracking