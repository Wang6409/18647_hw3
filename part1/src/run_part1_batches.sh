#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")"
LOG_FILE="${LOG_FILE:-part1_run.log}"
touch "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Part 1 batch run: $(date -Is) ==="
echo "Host: $(hostname)"
echo "Python: $(command -v python || command -v python3 || echo unavailable)"
python --version 2>&1 || python3 --version

submit_and_wait() {
    local label="$1"
    local script="$2"
    local output
    local job_ids
    local accounting=""

    echo "=== $label submission started: $(date -Is) ==="
    output="$(bash "$script")"
    printf '%s\n' "$output"
    job_ids="$(printf '%s\n' "$output" |
        sed -n 's/^Submitted batch job \([0-9][0-9]*\)$/\1/p' |
        paste -sd, -)"
    if [[ -z "$job_ids" ]]; then
        echo "Could not parse Slurm job IDs from $script output; stopping."
        return 1
    fi
    echo "$label Job IDs: $job_ids"

    while [[ -n "$(squeue -h -j "$job_ids")" ]]; do
        echo "$label still queued or running: $(date -Is)"
        sleep 60
    done
    echo "=== $label left the queue: $(date -Is) ==="

    for attempt in {1..12}; do
        accounting="$(sacct --noheader --parsable2 -X -j "$job_ids" \
            --format=State,ExitCode,Elapsed,MaxRSS,ReqMem)"
        if [[ -n "$accounting" ]]; then
            break
        fi
        echo "Waiting for accounting data ($attempt/12)..."
        sleep 10
    done
    if [[ -z "$accounting" ]]; then
        echo "No sacct records found for $label ($job_ids); stopping."
        return 1
    fi

    echo "=== $label sacct statistics ==="
    printf '%s\n' "$accounting" | awk -F'|' \
        'BEGIN { print "State|ExitCode|Elapsed|MaxRSS|ReqMem" } { print }'
    if ! printf '%s\n' "$accounting" |
        awk -F'|' 'NF >= 2 { n++; if ($1 != "COMPLETED" || $2 != "0:0") bad=1 }
            END { if (n == 0 || bad) exit 1 }'; then
        echo "$label has incomplete or failed task records; stopping."
        return 1
    fi
    echo "=== $label completed successfully: $(date -Is) ==="
}

START_BATCH="${START_BATCH:-1}"
case "$START_BATCH" in
    1)
        submit_and_wait "Batch 1 (IDs 1-5000)" "submit_0-4000.sh"
        submit_and_wait "Batch 2 (IDs 5001-10000)" "submit_5000-9000.sh"
        ;;
    2)
        submit_and_wait "Batch 2 (IDs 5001-10000)" "submit_5000-9000.sh"
        ;;
    *)
        echo "START_BATCH must be 1 or 2, got: $START_BATCH"
        exit 2
        ;;
esac
echo "=== Requested batches completed successfully: $(date -Is) ==="
