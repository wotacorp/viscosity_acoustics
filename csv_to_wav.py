import numpy as np
import pandas as pd
from scipy.io.wavfile import write
import os

# === CONFIGURATION ===
data_dir = './mic_data'
csv_file = 'mic_diff_5000Hz_20250619_165727_20250619_165727.csv'
wav_file = 'audio/' + csv_file.split('.')[0] + '.wav'

sampling_rate_str = csv_file.split('_')[2]  # e.g., '1000Hz'
sampling_rate = int(''.join(filter(str.isdigit, sampling_rate_str)))

vref = 3.3  # voltage reference

# === LOAD CSV ===
df = pd.read_csv(os.path.join(data_dir, csv_file))
voltages = df['Voltage_V'].values

# === NORMALIZE to -1.0 to 1.0 ===
# Shift around 0V, assuming Vref/2 is "zero"
centered = voltages - (vref / 2)
normalized = centered / (vref / 2)
clipped = np.clip(normalized, -1.0, 1.0)  # ensure no clipping artifacts

# === CONVERT to 16-bit PCM ===
pcm = (clipped * 32767).astype(np.int16)

# === WRITE WAV FILE ===
write(wav_file, sampling_rate, pcm)
print(f"WAV file saved as {wav_file} with sampling rate {sampling_rate}")