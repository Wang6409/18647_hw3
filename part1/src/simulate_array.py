"""Run one Slurm-array Lorenz trajectory."""

import os
from pathlib import Path

from lorenz import DT, integrate, load_endpoint, perturb_endpoint, write_csv

STEPS = 1_000
ENDPOINT_FILE = Path(os.environ.get("ENDPOINT_FILE", "baseline_endpoint.json"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "results"))


def main() -> None:
    try:
        task_id = int(os.environ["SLURM_ARRAY_TASK_ID"])
    except KeyError as error:
        raise RuntimeError("SLURM_ARRAY_TASK_ID is not set") from error
    task_id += int(os.environ.get("TASK_OFFSET", "0"))
    if task_id < 1 or task_id > 10_000:
        raise ValueError(f"array task ID must be in 1..10000, got {task_id}")

    endpoint = load_endpoint(ENDPOINT_FILE)
    initial_state = perturb_endpoint(endpoint, task_id)
    times, states = integrate(initial_state, STEPS, DT)
    output_path = OUTPUT_DIR / f"traj_{task_id:05d}.csv"
    write_csv(output_path, times, states)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
