import subprocess
import time

# Start acquisition on Raspberry Pi
acquire_cmd = [
    "ssh", "wota@accelero.local",
    "bash -c 'source /home/wota/code/.venv/bin/activate && python /home/wota/code/mic_recorder.py --duration 5 --frequency 1000'"
]
acquire_proc = subprocess.Popen(acquire_cmd)

# Optional delay
# time.sleep(1)

# Start local tone
# tone_proc = subprocess.run(["python", "speaker_test.py", "tone", "300", "15", "40"])
sweep_proc = subprocess.run(["python", "speaker_test.py", "sweep", "300", "500", "5", "40"])

# Wait for acquisition to finish
acquire_proc.wait()