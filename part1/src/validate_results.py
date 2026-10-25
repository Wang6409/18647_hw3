"""Check the expected Part 1 trajectory CSV files."""

import argparse
import csv
import math
from pathlib import Path

from lorenz import CSV_HEADER, DT

STEPS = 1_000
FIRST_ID = 1
LAST_ID = 10_000
RESULTS_DIR = Path("results")


def validate_csv(path: Path, steps: int = STEPS, dt: float = DT) -> None:
    with path.open(newline="", encoding="utf-8") as input_file:
        reader = csv.reader(input_file)
        if tuple(next(reader, ())) != CSV_HEADER:
            raise ValueError(f"{path}: incorrect or missing CSV header")

        rows = 0
        for rows, row in enumerate(reader, start=1):
            if len(row) != 4:
                raise ValueError(f"{path}: row {rows + 1} does not have four columns")
            try:
                time_value, x, y, z = (float(value) for value in row)
            except ValueError as error:
                raise ValueError(f"{path}: non-numeric row {rows + 1}") from error
            if not all(math.isfinite(value) for value in (time_value, x, y, z)):
                raise ValueError(f"{path}: non-finite value at row {rows + 1}")
            if not math.isclose(
                time_value, (rows - 1) * dt, rel_tol=1e-9, abs_tol=1e-10
            ):
                raise ValueError(f"{path}: unexpected time at row {rows + 1}")

        if rows != steps + 1:
            raise ValueError(f"{path}: expected {steps + 1} states, found {rows}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--first-id", type=int, default=FIRST_ID)
    parser.add_argument("--last-id", type=int, default=LAST_ID)
    parser.add_argument("--steps", type=int, default=STEPS)
    parser.add_argument("--dt", type=float, default=DT)
    args = parser.parse_args()
    if args.first_id < FIRST_ID or args.last_id < args.first_id:
        raise ValueError("task ID range must satisfy 1 <= first-id <= last-id")

    expected = {
        f"traj_{task_id:05d}.csv"
        for task_id in range(args.first_id, args.last_id + 1)
    }
    actual = {path.name for path in args.results_dir.glob("traj_*.csv")}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        raise ValueError(
            f"CSV set mismatch: expected {len(expected)}, found {len(actual)}; "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}"
        )

    for filename in sorted(expected):
        validate_csv(args.results_dir / filename, args.steps, args.dt)
    print(f"Validated {len(expected)} files with {args.steps + 1} states each.")


if __name__ == "__main__":
    main()
