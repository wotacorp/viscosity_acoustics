import pandas as pd
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("csv_file", help="CSV file to analyze")
parser.add_argument("--plot", action="store_true", help="Enable plotting")
args = parser.parse_args()

# Load the CSV file
df = pd.read_csv(args.csv_file)

print(f"Number of zeros: {len(df[df['Voltage_V'] == 0])}")
# Ensure the timestamp column exists
if 'Timestamp_s' not in df.columns:
    raise ValueError("CSV does not contain 'Timestamp_s' column")

# Calculate the time differences between each sample
time_diffs = df['Timestamp_s'].diff().dropna()

df['delta_t'] = time_diffs

# Compute actual sampling frequency statistics
mean_interval = time_diffs.mean()
actual_frequency = 1 / mean_interval

print(f"Average time between samples: {mean_interval:.6f} seconds")
print(f"Estimated sampling frequency: {actual_frequency:.2f} Hz")

# Optional: Check how consistent the intervals are
print(f"Standard deviation of intervals: {time_diffs.std():.6f} seconds")

# ---------------- Spike detection and statistics ----------------
# Define a spike as any Δt that is more than mean + 3·std above average
threshold = mean_interval + 3 * time_diffs.std()
spike_indices = df.index[df['delta_t'] > threshold]

if len(spike_indices) >= 2:
    spike_times = df.loc[spike_indices, 'Timestamp_s']
    spike_intervals = spike_times.diff().dropna()
    mean_spike_period = spike_intervals.mean()
    print(f"\nΔt spike threshold:        {threshold:.6f} s")
    print(f"Number of spikes detected: {len(spike_indices)}")
    print(f"Average time between spikes: {mean_spike_period:.4f} s ({1/mean_spike_period:.2f} Hz)")
else:
    print("\nNo spikes detected with the current threshold.")

# Check total duration and sample count
duration = df['Timestamp_s'].iloc[-1] - df['Timestamp_s'].iloc[0]
print(f"Total duration from timestamps: {duration:.6f} seconds")
print(f"Sample count: {len(df)}")
print(f"Expected count at 1000 Hz: {int(duration * 1000)}")

# Optional: Visualize delta_t consistency
if True:
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 4))
    plt.plot(df['Timestamp_s'].iloc[1:], df['delta_t'].iloc[1:], marker='.', linestyle='none', label='Δt')
    if len(spike_indices) > 0:
        plt.plot(df.loc[spike_indices, 'Timestamp_s'], df.loc[spike_indices, 'delta_t'], 'rx', label='Spikes')
    plt.title("Inter-sample Interval (Δt) over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Δt (s)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()