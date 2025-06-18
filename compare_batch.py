import subprocess
import os
from datetime import datetime

# List of BATCH sizes to test
batch_sizes = [10, 20, 40, 50, 100]

# Fixed parameters
duration = 10  # seconds
frequency = 1000

for batch in batch_sizes:
    print(f"\n=== Running test with BATCH = {batch} ===")

    # Create a unique output filename for each run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"./mic_data/mic_batch{batch}_{timestamp}.csv"

    # Set environment variable so script.py can read it
    env = os.environ.copy()
    env['BATCH_SIZE'] = str(batch)

    # Run the acquisition script (edit if script.py needs args)
    subprocess.run([
        'python', 'script.py',
        '--frequency', str(frequency),
        '--duration', str(duration),
        '--output', output_file
    ], env=env)

    # Analyze with sr.py
    print(f"Analyzing: {output_file}")
    subprocess.run(['python', 'sr.py', output_file])