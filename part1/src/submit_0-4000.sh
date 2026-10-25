#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"
mkdir -p logs ../../results

for offset in {0..4000..1000}; do
    sbatch --array=1-1000%100 \
        --export=ALL,TASK_OFFSET="$offset" \
        run_lorenz_array.slurm
done
