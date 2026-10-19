"""
Training entry point for the Dream-State Learning project.
"""
import argparse
import json
from pathlib import Path
from typing import List, Tuple

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import DistilBertForMaskedLM, DistilBertTokenizerFast
from datasets import load_dataset

from config import Config
from models.trainer import Trainer
from utils.logger import get_logger

def parse_ratio(ratio_str: str) -> int:
    try:
        w, d = ratio_str.split(":")
        return int(w) + int(d)
    except Exception as exc:
        raise ValueError(f"Invalid ratio format '{ratio_str}'. Expected 'W:D'.") from exc

def build_dataloader(subset_name: str, tokenizer: DistilBertTokenizerFast, batch_size: int = 4, max_samples: int = 200) -> DataLoader:
    glue = load_dataset("glue", subset_name, split="train")
    glue = glue.select(range(min(max_samples, len(glue))))

    sentences: List[str] = []
    for record in glue:
        if "sentence1" in record and "sentence2" in record:
            sentences.append(f"{record['sentence1']} {record['sentence2']}")
        elif "sentence" in record:
            sentences.append(record["sentence"])
        else:
            sentences.append(str(record))

    tokenized = tokenizer(sentences, padding="max_length", truncation=True, max_length=64, return_tensors="pt")
    input_ids = tokenized["input_ids"]
    labels = input_ids.clone()
    dataset = TensorDataset(input_ids, labels)

    def collate_fn(batch: Tuple[torch.Tensor, torch.Tensor]):
        input_ids_batch = torch.stack([b[0] for b in batch])
        labels_batch = torch.stack([b[1] for b in batch])
        return {"input_ids": input_ids_batch, "labels": labels_batch}

    return DataLoader(dataset, batch_size=batch_size, collate_fn=collate_fn)

def save_checkpoint(model: torch.nn.Module, checkpoint_path: Path):
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)

def main():
    parser = argparse.ArgumentParser(description="Run the Wake/Dream training loop.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--mode", type=str, default="run")
    parser.add_argument("--seeds", type=str, default=None)
    parser.add_argument("--ratio", type=str, default=None)
    parser.add_argument("--warmup", type=int, default=None)
    parser.add_argument("--glue-subset", type=str, default="mrpc")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    config = Config()
    logger = get_logger(__name__, config=config, log_to_file=False)

    if args.ratio:
        config.dream_ratio = parse_ratio(args.ratio)
    if args.warmup is not None:
        config.warm_up_steps = args.warmup

    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForMaskedLM.from_pretrained("distilbert-base-uncased")
    device = torch.device("cpu")
    model.to(device)

    dataloader = build_dataloader(subset_name=args.glue_subset, tokenizer=tokenizer)

    def run_one(seed: int) -> Tuple[int, Path]:
        torch.manual_seed(seed)
        # Pass tokenizer to Trainer
        trainer = Trainer(model=model, config=config, device=device, tokenizer=tokenizer)
        logger.info(f"Starting training for seed {seed}")
        metrics = trainer.run_training_loop(dataloader, max_steps=args.steps)

        ckpt_path = Path("data/checkpoints") / f"checkpoint_seed_{seed}_step_{len(metrics)}.pt"
        save_checkpoint(model, ckpt_path)

        summary_path = Path("data/results") / f"training_summary_seed_{seed}.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary = {"seed": seed, "steps_completed": len(metrics), "final_loss": metrics[-1]["loss"] if metrics else None, "checkpoint": str(ckpt_path)}
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        return len(metrics), summary_path

    if args.seeds:
        seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
        for s in seeds:
            run_one(s)
    else:
        run_one(args.seed)

if __name__ == "__main__":
    main()