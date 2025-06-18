#!/usr/bin/env python3
"""
Simple Contact Microphone Recorder
Records amplified contact microphone signals via MCP3008 differential mode
Usage: python3 mic_recorder.py --frequency 1000 --duration 30 --output mic_data.csv
"""

import time
import argparse
import csv
import numpy as np
from collections import deque
from datetime import datetime
import sys

try:
    import Adafruit_MCP3008
    import Adafruit_GPIO.SPI as SPI
except ImportError:
    print("Error: Please install required libraries:")
    print("sudo pip3 install Adafruit-MCP3008")
    sys.exit(1)

class ContactMicRecorder:
    def __init__(self, frequency=1000, variance_window=5.0):
        """
        Initialize contact microphone recorder

        Args:
            frequency (int): Sampling frequency in Hz
            variance_window (float): Rolling variance window in seconds
        """
        self.frequency = frequency
        self.sample_interval = 1.0 / frequency
        self.variance_window = variance_window
        self.variance_samples = int(variance_window * frequency)

        # Initialize MCP3008 with hardware SPI
        try:
            self.mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 0))
            print(f"✓ MCP3008 initialized (Hardware SPI)")
        except:
            print("✗ Failed to initialize MCP3008")
            print("  Make sure SPI is enabled: sudo raspi-config → Interface Options → SPI")
            sys.exit(1)

        # Rolling buffer for variance calculation
        self.voltage_buffer = deque(maxlen=self.variance_samples)

        print(f"✓ Frequency: {frequency} Hz")
        print(f"✓ Variance window: {variance_window} seconds ({self.variance_samples} samples)")

    def read_differential(self):
        """Read differential voltage (CH0 - CH1)"""
        try:
            # Read differential between CH0 and CH1
            raw_value = self.mcp.read_adc_difference(0)  # CH0-CH1
            # Convert to voltage (10-bit, VREF=3.3V)
            voltage = (raw_value / 1023.0) * 3.3
            return voltage, raw_value
        except Exception as e:
            print(f"Error reading ADC: {e}")
            return None, None

    def calculate_variance(self):
        """Calculate rolling variance"""
        if len(self.voltage_buffer) < 2:
            return 0.0
        return np.var(list(self.voltage_buffer))

    def record(self, duration, output_file, show_live=True):
        """
        Record microphone data

        Args:
            duration (float): Recording duration in seconds
            output_file (str): CSV output filename
            show_live (bool): Show live readings
        """
        print(f"\nStarting recording for {duration} seconds...")

        if show_live:
            print("\nLive readings (Voltage | Variance | Samples):")
            print("-" * 50)

        # Prepare data storage (pre-allocate for speed)
        max_samples = int(duration * self.frequency * 1.2)  # 20% buffer
        timestamps = []
        voltages = []
        raw_values = []
        variances = []

        # Batch data for CSV writing
        csv_batch = []

        # Open CSV file for writing
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp_s', 'Voltage_V', 'Raw_ADC', 'Rolling_Variance'])

            start_time = time.time()
            sample_count = 0
            last_display = 0

            try:
                while True:
                    current_time = time.time()
                    elapsed = current_time - start_time

                    if elapsed >= duration:
                        break

                    # Read sample
                    voltage, raw_value = self.read_differential()

                    if voltage is not None:
                        # Store data
                        timestamps.append(elapsed)
                        voltages.append(voltage)
                        raw_values.append(raw_value)

                        # Update rolling buffer
                        self.voltage_buffer.append(voltage)
                        variance = self.calculate_variance()
                        variances.append(variance)

                        # Batch CSV data
                        csv_batch.append([elapsed, voltage, raw_value, variance])

                        sample_count += 1

                        # Write CSV batch every 50 samples (more frequent for safety)
                        if len(csv_batch) >= 50:
                            for row in csv_batch:
                                writer.writerow([f"{row[0]:.6f}", f"{row[1]:.6f}", row[2], f"{row[3]:.8f}"])
                            csv_batch = []
                            csvfile.flush()

                        # Live display (every 200ms to reduce overhead)
                        if show_live and (current_time - last_display) >= 0.2:
                            print(f"\r{voltage:+8.4f}V | {variance:10.6f} | {sample_count:6d}", end='', flush=True)
                            last_display = current_time

                    # No artificial delay - run as fast as possible

            except KeyboardInterrupt:
                print(f"\n\nRecording stopped by user (Ctrl+C)")

            # Write remaining CSV data
            if csv_batch:
                for row in csv_batch:
                    writer.writerow([f"{row[0]:.6f}", f"{row[1]:.6f}", row[2], f"{row[3]:.8f}"])
                csvfile.flush()

        # Calculate final statistics
        actual_duration = timestamps[-1] if timestamps else 0
        actual_frequency = len(timestamps) / actual_duration if actual_duration > 0 else 0

        print(f"\n\n{'='*50}")
        print(f"Recording Complete!")
        print(f"{'='*50}")
        print(f"Duration:        {actual_duration:.2f} seconds")
        print(f"Samples:         {len(timestamps)}")
        print(f"Actual freq:     {actual_frequency:.1f} Hz")
        print(f"Mean voltage:    {np.mean(voltages):.4f} V")
        print(f"Std deviation:   {np.std(voltages):.4f} V")
        print(f"Min voltage:     {np.min(voltages):.4f} V")
        print(f"Max voltage:     {np.max(voltages):.4f} V")
        print(f"Final variance:  {variances[-1]:.6f}")
        print(f"Data saved to:   {output_file}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Contact Microphone Recorder (MCP3008 Differential Mode)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '-f', '--frequency',
        type=int,
        default=1000,
        help='Sampling frequency in Hz'
    )

    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=10.0,
        help='Recording duration in seconds'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output CSV filename (default: auto-generated)'
    )

    parser.add_argument(
        '-w', '--window',
        type=float,
        default=5.0,
        help='Rolling variance window in seconds'
    )

    parser.add_argument(
        '--no-live',
        action='store_true',
        help='Disable live display (faster recording)'
    )

    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()

    # Generate filename if not provided
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"mic_diff_{args.frequency}Hz_{timestamp}.csv"

    print("=" * 60)
    print("Contact Microphone Recorder - Differential Mode")
    print("=" * 60)
    print(f"Frequency:     {args.frequency} Hz")
    print(f"Duration:      {args.duration} s")
    print(f"Variance win:  {args.window} s")
    print(f"Output:        {args.output}")
    print(f"Live display:  {'No' if args.no_live else 'Yes'}")
    print("=" * 60)

    # Initialize recorder
    recorder = ContactMicRecorder(
        frequency=args.frequency,
        variance_window=args.window
    )

    # Start recording
    recorder.record(
        duration=args.duration,
        output_file=args.output,
        show_live=not args.no_live
    )

if __name__ == "__main__":
    main()
