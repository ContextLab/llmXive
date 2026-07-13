# llmXive Follow-up: Extending Moebius 0.2B

This project implements a dynamic rank adjustment mechanism for the Moebius 0.2B lightweight image inpainting framework.

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure environment (optional, defaults to CI mode):
 ```bash
 export MODE=ci # or 'research'
 ```

3. Run the data pipeline:
 ```bash
 python code/data/annotator.py
 ```

4. Validate proxy:
 ```bash
 python code/eval/stats.py --mode ci
 ```

## Project Structure
See `structure.txt` for the full directory layout.

## License
Research use only.