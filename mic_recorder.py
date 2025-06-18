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
import os

try:
    import Adafruit_MCP3008
    import Adafruit_GPIO.SPI as SPI

    if not os.path.exists("./mic_data"):
        os.makedirs("./mic_data")
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

        # For rolling Welford variance
        self.mean = 0.0
        self.M2 = 0.0
        self.n = 0

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
        """Calculate rolling variance using Welford's algorithm"""
        return self.M2 / self.n if self.n > 1 else 0.0

    def record(self, duration, output_file, show_live=True, rotate_minutes=1.0):
        """
        Record microphone data at a steady rate using busy-wait timing with CSV rotation.
        """
        import threading
        from queue import Queue

        print(f"\nStarting recording for {duration} seconds...")
        if show_live:
            print("\nLive readings (Voltage | Variance | Samples):")
            print("-" * 50)

        queue = Queue()
        stop_signal = object()

        def writer_worker(base_filename):
            file_count = 0
            writer = None
            csvfile = None
            next_rotate_time = time.perf_counter() + (rotate_minutes * 60.0)

            def open_new_file():
                nonlocal writer, csvfile, file_count, next_rotate_time
                if csvfile:
                    csvfile.close()
                suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{base_filename.rsplit('.', 1)[0]}_{suffix}.csv"
                csvfile = open(filename, 'w', newline='')
                writer = csv.writer(csvfile)
                writer.writerow(['Timestamp_s', 'Voltage_V', 'Raw_ADC', 'Rolling_Variance'])
                next_rotate_time = time.perf_counter() + (rotate_minutes * 60.0)

            open_new_file()

            while True:
                item = queue.get()
                if item is stop_signal:
                    break
                timestamp, voltage, raw, var = item
                if time.perf_counter() >= next_rotate_time and rotate_minutes > 0:
                    open_new_file()
                writer.writerow([f"{timestamp:.6f}", f"{voltage:.6f}", raw, f"{var:.8f}"])
                queue.task_done()

            if csvfile:
                csvfile.close()

        writer_thread = threading.Thread(target=writer_worker, args=(output_file,))
        writer_thread.start()

        total_samples = int(duration * self.frequency)
        start_time = time.perf_counter()
        next_time = start_time
        last_display = start_time
        sample_count = 0

        try:
            while True:
                now = time.perf_counter()
                if now < next_time:
                    continue

                voltage, raw = self.read_differential()
                timestamp = now - start_time

                x = voltage
                if self.n < self.variance_samples:
                    self.n += 1
                    delta = x - self.mean
                    self.mean += delta / self.n
                    delta2 = x - self.mean
                    self.M2 += delta * delta2
                    self.voltage_buffer.append(x)
                else:
                    old = self.voltage_buffer.popleft()
                    self.voltage_buffer.append(x)
                    old_mean = self.mean
                    delta_old = old - old_mean
                    self.mean = ((self.mean * self.n) - old + x) / self.n
                    delta_new = x - self.mean
                    delta_old2 = old - self.mean
                    self.M2 += delta_new * (x - self.mean) - delta_old * delta_old2

                var = self.calculate_variance()

                queue.put((timestamp, voltage, raw, var))
                sample_count += 1

                if show_live and (now - last_display) >= 0.2:
                    print(f"\r{voltage:+8.4f}V | {var:10.6f} | {sample_count:6d}", end='', flush=True)
                    last_display = now

                next_time += self.sample_interval

                if timestamp >= duration or sample_count >= total_samples:
                    break

        except KeyboardInterrupt:
            print(f"\n\nRecording stopped by user (Ctrl+C)")

        queue.put(stop_signal)
        writer_thread.join()

        print(f"\n\n{'='*50}")
        print(f"Recording Complete!")
        print(f"{'='*50}")
        print(f"Samples:         {sample_count}")
        print(f"Duration:        {timestamp:.2f} seconds")
        print(f"Data saved to:   Rotating files with base name: {output_file}")

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

    parser.add_argument(
        '-r', '--rotate',
        type=float,
        default=1.0,
        help='CSV rotation interval in minutes (0 = single file)'
    )

    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()

    # Generate filename if not provided
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"/home/wota/code/mic_data/mic_diff_{args.frequency}Hz_{timestamp}.csv"

    print("=" * 60)
    print("Contact Microphone Recorder - Differential Mode")
    print("=" * 60)
    print(f"Frequency:     {args.frequency} Hz")
    print(f"Duration:      {args.duration} s")
    print(f"Variance win:  {args.window} s")
    print(f"Output:        {args.output}")
    print(f"Live display:  {'No' if args.no_live else 'Yes'}")
    print(f"Rotate every:  {args.rotate} min")
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
        show_live=not args.no_live,
        rotate_minutes=args.rotate
    )

if __name__ == "__main__":
    main()
