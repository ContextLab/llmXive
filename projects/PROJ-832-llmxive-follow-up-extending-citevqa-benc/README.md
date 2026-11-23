# llmXive: CiteVQA Follow-up Research Project

This project implements an automated science pipeline to evaluate and extend the "CiteVQA" benchmark. It focuses on text-only retrieval, cross-modal spatial grounding, and visual-only localization control experiments using CPU-tractable LLMs.

## Project Structure

```
.
├── code/ # Core implementation logic
│ ├── config.py # Configuration management
│ ├── metrics.py # IoU, Semantic Similarity, SAA, VLA calculations
│ ├── retriever.py # Text retrieval using Sentence Transformers
│ ├── reasoning.py # LLM reasoning pipeline (Phi-3)
│ ├── visual_control.py # Visual-only localization experiment
│ ├── main.py # Orchestration script
│ └──... # Analysis and utility modules
├── tests/ # Unit, integration, and contract tests
├── data/
│ ├── raw/ # Raw downloaded data (PDFs, CSVs)
│ ├── processed/ # Parsed and structured data
│ ├── results/ # Evaluation outputs and plots
│ ├── logs/ # Runtime and memory logs
│ └── verified_sources.json # Verified data source URLs
├── scripts/ # Helper scripts
├── requirements.txt # Python dependencies
├── quickstart.md # Step-by-step setup guide
└── README.md # This file
```

## Key Features

- **Text-Only Pipeline**: Two-stage retrieval and reasoning using `all-MiniLM-L6-v2` and `Phi-3-mini`.
- **Spatial Grounding**: Evaluation of Strict Attributed Accuracy (SAA) via bounding box IoU.
- **Visual Control**: Comparison against a visual-only localization baseline using `Phi-3-vision`.
- **Statistical Rigor**: One-sample t-tests and bootstrap confidence intervals against a fixed baseline.
- **CPU Optimization**: All models quantized to 4-bit to run within standard CPU memory constraints (<7GB).

## Quick Start

1. **Setup**: Follow the instructions in [`quickstart.md`](quickstart.md) to install dependencies and fetch data.
2. **Run Evaluation**:
 ```bash
 python code/main.py --mode text_eval
 python code/main.py --mode saa_eval
 python code/main.py --mode visual_eval
 ```
3. **View Results**: Check `data/results/` for JSON outputs and plots.

## Configuration

All hyperparameters, paths, and seeds are managed in `code/config.py`.
- **Models**: `all-MiniLM-L6-v2` (Retriever), `Phi-3-mini` (Reasoner), `Phi-3-vision` (Visual).
- **Thresholds**: Semantic Similarity >= 0.85, IoU > 0.5 for SAA.

## Testing

Run the full test suite:
```bash
pytest tests/ -v
```

## Contributing

Please ensure all new code adheres to the project's linting (`ruff`) and formatting (`black`) standards.

## License

[Insert License Here]
