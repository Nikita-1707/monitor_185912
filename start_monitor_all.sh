#!/bin/bash

# Run commands in parallel
python3 monitor.py >> ~/log_m &
python3 monitor_tai.py >> ~/log_tai &
python3 monitor_madr.py >> ~/log_madr &
python3 monitor_bars.py >> ~/log_bars &

# Wait for all background jobs to finish
wait