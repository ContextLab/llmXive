import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import sys

def load_params(params_file):
    with open(params_file, 'r') as f:
        params = json.load(f)
    return params

def generate_thermal_data(mean, scale, num_samples=1000):
    data = np.random.normal(mean, scale, num_samples)
    df = pd.DataFrame({'value': data})
    return df

def generate_nonthermal_data(shape, num_samples=1000):
    data = np.random.pareto(shape, num_samples)
    df = pd.DataFrame({'value': data})
    return df

def main():
    parser = argparse.ArgumentParser(description='Generate test thermal and nonthermal data.')
    parser.add_argument('--params-file', type=str, default='artifacts/test_params.json', help='Path to the parameters file.')
    parser.add_argument('--thermal-output', type=str, default='data/derived/test_thermal_data.csv', help='Path to save thermal data.')
    parser.add_argument('--nonthermal-output', type=str, default='data/derived/test_nonthermal_data.csv', help='Path to save nonthermal data.')

    args = parser.parse_args()

    params = load_params(args.params_file)
    mean = params['maxwell_boltzmann']['mean']
    scale = params['maxwell_boltzmann']['scale']
    shape = params['pareto']['shape']

    thermal_data = generate_thermal_data(mean, scale)
    nonthermal_data = generate_nonthermal_data(shape)

    thermal_data.to_csv(args.thermal_output, index=False)
    nonthermal_data.to_csv(args.nonthermal_output, index=False)

    print(f"Thermal data saved to {args.thermal_output}")
    print(f"Nonthermal data saved to {args.nonthermal_output}")

if __name__ == '__main__':
    main()