import csv
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from lorenz import (
    BETA,
    DT,
    RHO,
    derivative,
    integrate,
    load_endpoint,
    perturb_endpoint,
    save_endpoint,
    write_csv,
)
from validate_results import validate_csv


class LorenzTests(unittest.TestCase):
    def test_nonzero_fixed_points_satisfy_system(self):
        coordinate = math.sqrt(BETA * (RHO - 1.0))
        for sign in (-1.0, 1.0):
            state = (sign * coordinate, sign * coordinate, RHO - 1.0)
            self.assertTrue(all(abs(value) < 1e-12 for value in derivative(0, state)))

    def test_integrate_returns_initial_and_all_requested_samples(self):
        times, states = integrate((1.0, 1.0, 1.0), steps=7, dt=DT)
        self.assertEqual(len(times), 8)
        self.assertEqual(states.shape, (8, 3))
        np.testing.assert_array_equal(states[0], (1.0, 1.0, 1.0))
        self.assertAlmostEqual(times[-1], 7 * DT)
        self.assertTrue(np.isfinite(states).all())

    def test_perturbation_is_reproducible_and_bounded(self):
        endpoint = (1.0, 2.0, 3.0)
        first = perturb_endpoint(endpoint, task_id=42)
        np.testing.assert_array_equal(first, perturb_endpoint(endpoint, task_id=42))
        self.assertLessEqual(float(np.linalg.norm(first - endpoint)), 0.5)
        self.assertFalse(np.array_equal(first, perturb_endpoint(endpoint, task_id=43)))

    def test_endpoint_round_trip_and_csv_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            endpoint = (1.0, 2.0, 3.0)
            endpoint_path = root / "endpoint.json"
            save_endpoint(endpoint_path, endpoint)
            self.assertEqual(load_endpoint(endpoint_path), endpoint)

            times, states = integrate(endpoint, steps=3, dt=DT)
            csv_path = root / "traj_00001.csv"
            write_csv(csv_path, times, states)
            validate_csv(csv_path, steps=3, dt=DT)

            replacement_times, replacement_states = integrate(
                (4.0, 5.0, 6.0), steps=2, dt=DT
            )
            write_csv(csv_path, replacement_times, replacement_states)
            validate_csv(csv_path, steps=2, dt=DT)
            with csv_path.open(newline="", encoding="utf-8") as input_file:
                self.assertEqual(len(list(csv.reader(input_file))), 4)

            with csv_path.open("a", encoding="utf-8") as output_file:
                output_file.write("0.03,1,2,3\n")
            with self.assertRaisesRegex(ValueError, "expected 3 states"):
                validate_csv(csv_path, steps=2, dt=DT)


if __name__ == "__main__":
    unittest.main()
