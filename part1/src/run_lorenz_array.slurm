#!/bin/bash
#SBATCH --job-name=lorenz
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --array=1-10000%100
#SBATCH --output=logs/lorenz_%A_%a.log
#SBATCH --error=logs/lorenz_%A_%a.err

set -euo pipefail

cd "${SLURM_SUBMIT_DIR}"

ENDPOINT_FILE="${ENDPOINT_FILE:-${SLURM_SUBMIT_DIR}/../../data/baseline_endpoint.json}"
OUTPUT_DIR="${OUTPUT_DIR:-${SLURM_SUBMIT_DIR}/../../results}"
PYTHON="${PYTHON:-${SLURM_SUBMIT_DIR}/../../venv-18647/bin/python}"

export TASK_OFFSET="${TASK_OFFSET:-0}"
export ENDPOINT_FILE OUTPUT_DIR
"${PYTHON}" simulate_array.py
