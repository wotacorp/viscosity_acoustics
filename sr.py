import pandas as pd

# Load the CSV file
df = pd.read_csv('mic_diff_1000Hz_20250618_113300.csv')

# Ensure the timestamp column exists
if 'Timestamp_s' not in df.columns:
    raise ValueError("CSV does not contain 'Timestamp_s' column")

# Calculate the time differences between each sample
time_diffs = df['Timestamp_s'].diff().dropna()

# Compute actual sampling frequency statistics
mean_interval = time_diffs.mean()
actual_frequency = 1 / mean_interval

print(f"Average time between samples: {mean_interval:.6f} seconds")
print(f"Estimated sampling frequency: {actual_frequency:.2f} Hz")

# Optional: Check how consistent the intervals are
print(f"Standard deviation of intervals: {time_diffs.std():.6f} seconds")