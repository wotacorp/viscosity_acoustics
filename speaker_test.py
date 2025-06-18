#!/usr/bin/env python3
"""
Enhanced Frequency Generator - Command Line

Usage:
    python speaker_test.py [type] [parameters...]

Signal Types:
    tone [frequency] [duration] [volume]     # Pure sine wave (default)
    noise [duration] [volume]                # White noise
    sweep [start_freq] [end_freq] [duration] [volume]  # Frequency sweep

Examples:
    python speaker_test.py tone 1000 5 30    # 1000 Hz tone for 5s at 30% volume
    python speaker_test.py noise 10 50       # White noise for 10s at 50% volume
    python speaker_test.py sweep 100 2000 8 40  # 100-2000 Hz sweep over 8s at 40% volume
"""

import numpy as np
import pyaudio
import sys
import time

def generate_tone(frequency=1000, duration=10, volume=30):
    """
    Generate a pure sine wave tone
    
    Args:
        frequency: Frequency in Hz (default: 1000)
        duration: Duration in seconds (default: 10)
        volume: Volume percentage 0-100 (default: 30)
    """
    
    # Audio parameters
    sample_rate = 44100
    amplitude = volume / 100.0
    
    # Clamp values to safe ranges
    frequency = max(1, min(20000, frequency))
    amplitude = max(0.0, min(1.0, amplitude))
    duration = max(0.1, duration)
    
    print(f"Generating {frequency} Hz tone for {duration} seconds at {volume}% volume")
    
    # Initialize PyAudio
    try:
        p = pyaudio.PyAudio()
    except Exception as e:
        print(f"Error: Could not initialize audio system: {e}")
        print("Install PyAudio with: pip install pyaudio")
        return False
    
    try:
        # Open audio stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=0
        )
        
        # Calculate total samples
        total_samples = int(sample_rate * duration)
        chunk_size = 1024
        
        # Generate and play audio in chunks
        for i in range(0, total_samples, chunk_size):
            # Calculate samples for this chunk
            samples_left = min(chunk_size, total_samples - i)
            
            # Generate time array
            t = np.arange(i, i + samples_left) / sample_rate
            
            # Generate sine wave
            waveform = amplitude * np.sin(2 * np.pi * frequency * t)
            
            # Convert to bytes and play
            stream.write(waveform.astype(np.float32).tobytes())
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Tone completed")
        return True
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        p.terminate()
        return False

def generate_white_noise(duration=10, volume=30):
    """
    Generate white noise
    
    Args:
        duration: Duration in seconds (default: 10)
        volume: Volume percentage 0-100 (default: 30)
    """
    
    # Audio parameters
    sample_rate = 44100
    amplitude = volume / 100.0
    
    # Clamp values to safe ranges
    amplitude = max(0.0, min(1.0, amplitude))
    duration = max(0.1, duration)
    
    print(f"Generating white noise for {duration} seconds at {volume}% volume")
    
    # Initialize PyAudio
    try:
        p = pyaudio.PyAudio()
    except Exception as e:
        print(f"Error: Could not initialize audio system: {e}")
        print("Install PyAudio with: pip install pyaudio")
        return False
    
    try:
        # Open audio stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=0
        )
        
        # Calculate total samples
        total_samples = int(sample_rate * duration)
        chunk_size = 1024
        
        # Generate and play audio in chunks
        for i in range(0, total_samples, chunk_size):
            # Calculate samples for this chunk
            samples_left = min(chunk_size, total_samples - i)
            
            # Generate white noise (random values between -1 and 1)
            waveform = amplitude * (2 * np.random.random(samples_left) - 1)
            
            # Convert to bytes and play
            stream.write(waveform.astype(np.float32).tobytes())
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("White noise completed")
        return True
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        p.terminate()
        return False

def generate_frequency_sweep(start_freq=100, end_freq=2000, duration=10, volume=30, sweep_type='linear'):
    """
    Generate a frequency sweep (chirp)
    
    Args:
        start_freq: Starting frequency in Hz (default: 100)
        end_freq: Ending frequency in Hz (default: 2000)
        duration: Duration in seconds (default: 10)
        volume: Volume percentage 0-100 (default: 30)
        sweep_type: 'linear' or 'logarithmic' (default: 'linear')
    """
    
    # Audio parameters
    sample_rate = 44100
    amplitude = volume / 100.0
    
    # Clamp values to safe ranges
    start_freq = max(1, min(20000, start_freq))
    end_freq = max(1, min(20000, end_freq))
    amplitude = max(0.0, min(1.0, amplitude))
    duration = max(0.1, duration)
    
    print(f"Generating {sweep_type} frequency sweep from {start_freq} Hz to {end_freq} Hz")
    print(f"Duration: {duration} seconds at {volume}% volume")
    
    # Initialize PyAudio
    try:
        p = pyaudio.PyAudio()
    except Exception as e:
        print(f"Error: Could not initialize audio system: {e}")
        print("Install PyAudio with: pip install pyaudio")
        return False
    
    try:
        # Open audio stream
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            output=True,
            output_device_index=0
        )
        
        # Calculate total samples
        total_samples = int(sample_rate * duration)
        chunk_size = 1024
        
        # Generate and play audio in chunks
        for i in range(0, total_samples, chunk_size):
            # Calculate samples for this chunk
            samples_left = min(chunk_size, total_samples - i)
            
            # Generate time array for this chunk
            t_chunk = np.arange(i, i + samples_left) / sample_rate
            
            # Calculate instantaneous frequency for each sample
            if sweep_type == 'logarithmic':
                # Logarithmic sweep
                freq_ratio = end_freq / start_freq
                freq_instantaneous = start_freq * (freq_ratio ** (t_chunk / duration))
                # Phase calculation for logarithmic sweep
                phase = 2 * np.pi * start_freq * (duration / np.log(freq_ratio)) * (freq_ratio ** (t_chunk / duration) - 1)
            else:
                # Linear sweep (default)
                freq_instantaneous = start_freq + (end_freq - start_freq) * (t_chunk / duration)
                # Phase calculation for linear sweep
                phase = 2 * np.pi * (start_freq * t_chunk + 0.5 * (end_freq - start_freq) * (t_chunk ** 2) / duration)
            
            # Generate waveform
            waveform = amplitude * np.sin(phase)
            
            # Convert to bytes and play
            stream.write(waveform.astype(np.float32).tobytes())
        
        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        print("Frequency sweep completed")
        return True
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        p.terminate()
        return False

def show_usage():
    """Display usage information"""
    print("Usage:")
    print("  python speaker_test.py [type] [parameters...]")
    print()
    print("Signal Types:")
    print("  tone [frequency] [duration] [volume]           # Pure sine wave")
    print("  noise [duration] [volume]                      # White noise")
    print("  sweep [start_freq] [end_freq] [duration] [volume]  # Frequency sweep")
    print("  logsweep [start_freq] [end_freq] [duration] [volume]  # Logarithmic sweep")
    print()
    print("Examples:")
    print("  python speaker_test.py tone 1000 5 30          # 1000 Hz tone")
    print("  python speaker_test.py noise 10 50             # White noise")
    print("  python speaker_test.py sweep 100 2000 8 40     # Linear sweep")
    print("  python speaker_test.py logsweep 20 20000 10 30 # Log sweep")
    print("  python speaker_test.py 440                     # Backward compatibility")

def main():
    # Check for help request
    print("ok")
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        sys.exit(0)
    
    # Require at least signal type
    if len(sys.argv) < 2:
        print("Error: Signal type required")
        show_usage()
        sys.exit(1)
    
    signal_type = sys.argv[1].lower()
    
    try:
        if signal_type == "tone":
            # Default values for tone
            frequency = 1000
            duration = 10
            volume = 30
            
            if len(sys.argv) > 2:
                frequency = float(sys.argv[2])
                print(frequency)
            if len(sys.argv) > 3:
                duration = float(sys.argv[3])
            if len(sys.argv) > 4:
                volume = float(sys.argv[4])
            
            generate_tone(frequency, duration, volume)
        
        elif signal_type == "noise":
            # Default values for noise
            duration = 10
            volume = 30
            
            if len(sys.argv) > 2:
                duration = float(sys.argv[2])
            if len(sys.argv) > 3:
                volume = float(sys.argv[3])
            
            generate_white_noise(duration, volume)
        
        elif signal_type in ["sweep", "logsweep"]:
            # Default values for sweep
            start_freq = 100
            end_freq = 2000
            duration = 10
            volume = 30
            
            if len(sys.argv) > 2:
                start_freq = float(sys.argv[2])
            if len(sys.argv) > 3:
                end_freq = float(sys.argv[3])
            if len(sys.argv) > 4:
                duration = float(sys.argv[4])
            if len(sys.argv) > 5:
                volume = float(sys.argv[5])
            
            sweep_type = 'logarithmic' if signal_type == 'logsweep' else 'linear'
            generate_frequency_sweep(start_freq, end_freq, duration, volume, sweep_type)
        
        else:
            print(f"Error: Unknown signal type '{signal_type}'")
            print("Valid types: tone, noise, sweep, logsweep")
            sys.exit(1)
            
    except ValueError as e:
        print("Error: Invalid numeric parameters")
        print(f"Make sure all numbers are valid: {e}")
        sys.exit(1)
    except IndexError:
        print("Error: Missing required parameters")
        show_usage()
        sys.exit(1)

if __name__ == "__main__":
    main()