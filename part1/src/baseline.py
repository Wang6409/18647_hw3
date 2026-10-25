"""Run and plot the local 2,000-step Lorenz baseline."""

from pathlib import Path

import matplotlib.pyplot as plt

from lorenz import BETA, DT, RHO, integrate, save_endpoint, write_csv

STEPS = 2_000
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    times, states = integrate((1.0, 1.0, 1.0), STEPS, DT)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    write_csv(OUTPUT_DIR / "baseline.csv", times, states)
    save_endpoint(OUTPUT_DIR / "baseline_endpoint.json", states[-1])

    fixed_x = (BETA * (RHO - 1.0)) ** 0.5
    figure = plt.figure(figsize=(8, 6))
    axis = figure.add_subplot(111, projection="3d")
    axis.plot(states[:, 0], states[:, 1], states[:, 2], linewidth=0.6)
    axis.scatter(
        (fixed_x, -fixed_x),
        (fixed_x, -fixed_x),
        (RHO - 1.0, RHO - 1.0),
        color="red",
        marker="x",
        label="nonzero fixed points",
    )
    axis.set(xlabel="x", ylabel="y", zlabel="z", title="Lorenz baseline (2,000 steps)")
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "baseline_trajectory.png", dpi=180)
    plt.close(figure)

    print(f"Final time: {times[-1]:g}")
    print(f"Endpoint: {states[-1].tolist()}")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
