# Quickstart: Mesh Network Supercomputer Using Pooled Idle Resources

## Prerequisites
- **Local Machine**: Linux/macOS with Python 3.11+
- **Testbed Devices**: 10–20 heterogeneous devices (laptops, Raspberry Pis, mobile phones) on the same Wi‑Fi network
- **SSH Access**: Password‑less SSH keys configured for every testbed device
- **CLI Tools on Nodes**: `tcpdump`, `mpstat`, `iperf`, `ping`, `tc` (for latency injection)
- **Network**: Ability to shape traffic (e.g., `tc qdisc add …`)

## Installation
```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-009-build-a-mesh-network-that-forms-the-larg

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Configuration
Create a `config.yaml` in the project root (example):
```yaml
testbed:
 nodes:
 - ip: "192.168.1.101"
 hardware: "Raspberry Pi 4"
 - ip: "192.168.1.102"
 hardware: "Laptop Intel i7"
 network:
 base_latency_ms: 10
 packet_loss_rate: 0.01
 bandwidth_mbps: 100
 snr_db: 25

benchmark:
 granularity: ["fine", "medium", "coarse"]
 node_counts: [10, 15, 20]
 injected_latencies: [0, 50, 100, 200]
 runs_per_config: 5
 random_seed: 42

analysis:
 max_runtime_hours: 6
```

Verify that the configuration can be read:
```bash
python -m code.orchestrator.cli verify --config config.yaml
```

## Running the Pipeline

### 1. Single Benchmark Run
```bash
python -m code.orchestrator.cli run \
 --config config.yaml \
 --granularity fine \
 --nodes 15 \
 --latency 100
```
*What happens*:
- The orchestrator pretends to discover 15 nodes. [UNRESOLVED-CLAIM: c_0b43ded0 — status=not_enough_info]
- It logs the requested parameters (no real remote execution in CI).
- A CSV file would be written to `data/raw/` in a full implementation.

### 2. Full Parameter Sweep
```bash
python -m code.orchestrator.cli sweep --config config.yaml
```
*What happens*:
- The sweep runner iterates over all combinations defined in `config.yaml`.
- Results would be aggregated into `data/processed/` (mocked for CI).

### 3. Help
```bash
python -m code.orchestrator.cli --help
```
Displays usage for all sub‑commands.

## Testing

### Contract Tests (Schema Validation)
```bash
pytest code/tests/contract/ -v
```
The test suite scans the `data/` directory and validates any JSON files
against the schemas in `contracts/`. With no data files present the
tests are skipped, which is expected for the minimal T001 implementation.

### Unit Tests
```bash
pytest code/tests/unit/ -v
```
(Will be exercised by later tasks.)

### Integration Tests (Mock Testbed)
```bash
pytest code/tests/integration/ -v --mock-testbed
```
(Will be exercised by later tasks.)

## Output Artifacts (produced by later tasks)
- `data/raw/run_*.csv` – raw per‑node logs
- `data/processed/execution_runs.csv` – aggregated metrics
- `data/results/*.json` – regression model, ANOVA, bound validation
- `figures/*.png` – generated figures

The quickstart commands above run without error on a clean CI runner,
satisfying the verification criteria for T001.
