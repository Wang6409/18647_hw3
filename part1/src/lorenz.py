"""Shared Lorenz integration and CSV helpers for Part 1."""

import csv
import json
import math
from pathlib import Path
from typing import Sequence, Tuple

import numpy as np
from scipy.integrate import solve_ivp

SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.01
CSV_HEADER = ("time", "x", "y", "z")


def derivative(_time: float, state: Sequence[float]) -> Tuple[float, float, float]:
    x, y, z = state
    return (
        SIGMA * (y - x),
        x * (RHO - z) - y,
        x * y - BETA * z,
    )


def integrate(
    initial_state: Sequence[float],
    steps: int,
    dt: float = DT,
) -> Tuple[np.ndarray, np.ndarray]:
    if steps < 1:
        raise ValueError("steps must be positive")
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be a positive finite number")
    if len(initial_state) != 3 or not all(
        math.isfinite(float(value)) for value in initial_state
    ):
        raise ValueError("initial_state must contain three finite values")

    times = np.linspace(0.0, steps * dt, steps + 1)
    solution = solve_ivp(
        derivative,
        (0.0, steps * dt),
        initial_state,
        method="RK45",
        t_eval=times,
        rtol=1e-8,
        atol=1e-10,
    )
    if not solution.success:
        raise RuntimeError(f"Lorenz integration failed: {solution.message}")
    if solution.t.size != steps + 1 or solution.y.shape != (3, steps + 1):
        raise RuntimeError("Lorenz integration returned an incomplete trajectory")
    if not np.isfinite(solution.y).all():
        raise RuntimeError("Lorenz integration returned non-finite states")
    return solution.t, solution.y.T


def save_endpoint(path: Path, state: Sequence[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": [float(value) for value in state],
        "parameters": {"sigma": SIGMA, "rho": RHO, "beta": BETA},
        "dt": DT,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_endpoint(path: Path) -> Tuple[float, float, float]:
    with path.open(encoding="utf-8") as endpoint_file:
        payload = json.load(endpoint_file)
    state = payload.get("state")
    if not isinstance(state, list) or len(state) != 3:
        raise ValueError(f"{path} must contain a three-value 'state' array")
    endpoint = tuple(float(value) for value in state)
    if not all(math.isfinite(value) for value in endpoint):
        raise ValueError(f"{path} contains a non-finite endpoint")
    return endpoint[0], endpoint[1], endpoint[2]


def perturb_endpoint(
    endpoint: Sequence[float],
    task_id: int,
) -> np.ndarray:
    if task_id < 1:
        raise ValueError("task_id must be positive")
    rng = np.random.default_rng(task_id)
    direction = rng.normal(size=3)
    norm = np.linalg.norm(direction)
    if norm == 0:
        raise RuntimeError("random perturbation direction has zero length")
    direction /= norm
    return np.asarray(endpoint, dtype=float) + rng.uniform(0.0, 0.5) * direction


def write_csv(path: Path, times: Sequence[float], states: np.ndarray) -> None:
    if states.shape != (len(times), 3):
        raise ValueError("states must have three columns and match the time array")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(CSV_HEADER)
        writer.writerows(
            (time_value, state[0], state[1], state[2])
            for time_value, state in zip(times, states)
        )
