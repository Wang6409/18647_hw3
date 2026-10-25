# Part 1: Lorenz trajectories

Part 1 has two compute stages: first, run the 2,000-step initial simulation on
your PC/laptop as stated in the assignment; then copy its endpoint to PSC and
generate 10,000 perturbed 1,000-step trajectories with a Slurm job array.
The scripts use Python, SciPy's `solve_ivp` RK45 integrator, NumPy, and
Matplotlib for the local plot.

The requested output grid has spacing `dt=0.01`. A 2,000-step baseline has
2,001 sampled states through `t=20`; each 1,000-step batch trajectory has
1,001 sampled states through `t=10`, plus its CSV header. RK45 internally
uses adaptive steps; `t_eval` specifies the regularly spaced output times.

## 1. Run the baseline on your PC/laptop

From the repository root:

```powershell
python -m pip install -r part1\src\requirements.txt
python part1\src\baseline.py
```

This starts at `(1, 1, 1)` and creates:

- `part1\results\baseline.csv`
- `part1\results\baseline_endpoint.json`
- `part1\results\baseline_trajectory.png`

Inspect the plot to confirm the trajectory is on the Lorenz attractor. For
the classical parameters, the nonzero fixed points are
`(±sqrt(beta*(rho-1)), ±sqrt(beta*(rho-1)), rho-1)`, approximately
`(±8.485, ±8.485, 27)`. These fixed points are unstable at `rho=28`; describe
the trajectory as switching between the two lobes, not converging to a stable
fixed point. The endpoint JSON is the exact state used to seed the batch runs.

## 2. Upload the batch scripts and endpoint to PSC

Use the PSC login host and transfer method for your account. For example,
from PowerShell, replace the placeholders with your PSC account details and
working directory:

```powershell
scp part1\src\lorenz.py part1\src\simulate_array.py `
  part1\src\validate_results.py part1\src\run_lorenz_array.slurm `
  part1\src\requirements.txt part1\results\baseline_endpoint.json `
  <PSC_USER>@<PSC_HOST>:<PSC_WORKDIR>/
```

## 3. Check PSC limits and Python environment

Log in to Bridges-2 and check live settings:

```bash
scontrol show config | grep -i MaxArraySize
scontrol show partition RM-shared
sinfo -o "%P %a %l %D %c %m"
sacctmgr show assoc where user="$USER" format=Cluster,Account,User,Partition,QOS,MaxJobs,MaxSubmitJobs
module avail python
python3 --version
```

The code requires Python 3.8 or newer. The local baseline needs the packages
in `requirements.txt` (`numpy`, `scipy`, and `matplotlib`); the PSC array
script and validator need NumPy and SciPy. Use PSC modules if they provide
these packages. Otherwise, create an environment on PSC and install the
requirements using the package installation method supported there. Set
`PYTHON` to that environment's Python executable before `sbatch`, or add the
appropriate module-load commands to the Slurm script.

The array range `1-10000` requires `MaxArraySize >= 10001`, because the
largest legal index is `MaxArraySize - 1`. Account/QoS queries may be
restricted. If the array cap, partition, or account limits cannot be
confirmed, ask PSC or course staff before submitting. The Slurm script
defaults to `RM-shared`, one CPU per task, and at most 100 concurrent tasks;
adjust those settings to the current PSC/course requirements.

Check the Python version **inside the activated environment** used for the
job, not only the system `python3`. If the existing virtual environment was
created with Python older than 3.8, create a new environment using an available
Python 3.8+ module; activating an old environment does not upgrade its Python:

```bash
module load <available-python-3.8-or-newer-module>
python --version
python -m venv "$HOME/venvs/hw3"
source "$HOME/venvs/hw3/bin/activate"
python -m pip install -r requirements.txt
export PYTHON="$(command -v python)"
python -c "import numpy, scipy; print(numpy.__version__, scipy.__version__)"
```

Use the same module and environment when submitting jobs. If the module is not
loaded automatically for batch jobs, add its `module load` command near the
top of `run_lorenz_array.slurm`. Do not reuse a venv created with an older
Python interpreter.

If the confirmed array index cap is below 10,000, submit chunks that fit
within it and use `TASK_OFFSET` to keep the trajectory IDs consecutive. For
example, if `MaxArraySize=1001`:

```bash
sbatch --array=1-1000%100 --export=ALL,TASK_OFFSET=0 run_lorenz_array.slurm
sbatch --array=1-1000%100 --export=ALL,TASK_OFFSET=1000 run_lorenz_array.slurm
```

Continue with offsets `2000`, `3000`, etc., shortening the last range as
needed. Keep within the account's concurrent and submitted-job limits.

The two `submit_*.sh` scripts split the work into batches of 5,000 tasks.
To submit them sequentially, wait for the first batch, record its Slurm
accounting data, and then submit the second. The helper
`src/run_part1_batches.sh` automates this sequence and appends submission
times, job IDs, and `sacct` statistics to `src/part1_run.log`:

```bash
bash run_part1_batches.sh
```

If the helper stopped after the first batch was already submitted or finished,
resume without resubmitting it using:

```bash
START_BATCH=2 bash run_part1_batches.sh
```

The helper omits the `sacct --array` option for compatibility with PSC's
installed Slurm version.

## 4. Smoke-test and submit the array

In the PSC working directory, create the log and output directories before
submitting; Slurm opens the log file before the job script starts:

```bash
mkdir -p logs results
sbatch --test-only --array=1-10000%100 run_lorenz_array.slurm
sbatch --array=1-1 run_lorenz_array.slurm
```

`--test-only` checks that Slurm accepts the request but does not run it. Use
a chunk-sized range if the confirmed array cap is smaller. Wait for the
single-task job to succeed and check `results/traj_00001.csv`: it should have
the `time,x,y,z` header, 1,001 data rows, and times from 0 through 10. Remove
the smoke-test file before submitting the complete array:

```bash
rm results/traj_00001.csv
sbatch run_lorenz_array.slurm
squeue -u "$USER"
```

## 5. Verify and package the results

Use the job ID returned by `sbatch` to check task outcomes:

```bash
sacct -j JOB_ID --array -X --format=JobID,State,ExitCode
```

After the array finishes, validate all expected CSVs:

```bash
python3 validate_results.py --results-dir results \
  --first-id 1 --last-id 10000 --steps 1000 --dt 0.01
```

The validator checks filenames, headers, row counts, finite values, and
timestamps across roughly 10 million data rows. Package only the 10,000
batch CSVs (not the baseline CSV, endpoint, or plot) as `part1/results.zip`:

```bash
zip -j results.zip results/traj_*.csv
unzip -t results.zip
```

Download `results.zip` into the local `part1/` directory. Submit it together
with `part1/src/` in the required homework archive.
