#!/usr/bin/env python3
"""
Audio Frequency Discrimination Test
"""
import argparse
import sys
import time
import numpy as np
import sounddevice as sd
from scipy.optimize import curve_fit
from typing import List, Tuple, Optional

SAMPLE_RATE = 44100
DURATION = 0.8
SILENCE_DURATION = 0.4
VOLUME = 0.3

def generate_tone(frequency: float, duration: float, sample_rate: int) -> np.ndarray:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = np.sin(2 * np.pi * frequency * t)
    fade_len = int(0.02 * sample_rate)
    envelope = np.ones_like(wave)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    wave = wave * envelope * VOLUME
    return wave.astype(np.float32)

def play_tones(ref_freq: float, test_freq: float, order: int) -> None:
    tone_ref = generate_tone(ref_freq, DURATION, SAMPLE_RATE)
    tone_test = generate_tone(test_freq, DURATION, SAMPLE_RATE)
    silence = np.zeros(int(SAMPLE_RATE * SILENCE_DURATION), dtype=np.float32)
    if order == 0:
        sequence = [tone_ref, silence, tone_test]
    else:
        sequence = [tone_test, silence, tone_ref]
    audio = np.concatenate(sequence)
    sd.play(audio, samplerate=SAMPLE_RATE)
    sd.wait()

def psychometric_function(x, threshold, slope, guess=0.5, lapse=0.02):
    return guess + (1 - guess - lapse) / (1 + np.exp(-slope * (x - threshold)))

def fit_threshold(deltas: List[float], corrects: List[int]) -> Optional[float]:
    if len(set(deltas)) < 3:
        return None
    x = np.array(deltas)
    y = np.array(corrects, dtype=float)
    try:
        popt, _ = curve_fit(
            lambda x, th, sl: psychometric_function(x, th, sl),
            x, y, p0=[np.mean(deltas), 5.0],
            bounds=([0.1, 0.5], [20, 50])
        )
        return popt[0]
    except Exception:
        return None

def run_staircase(ref_freq: float, start_delta: float, min_delta: float,
                  max_trials: int, n_reversals: int) -> Tuple[List[float], List[int], List[float]]:
    delta = start_delta
    direction = -1
    last_correct = True
    reversal_deltas = []
    deltas, corrects = [], []
    reversal_count = 0
    rng = np.random.default_rng()

    for trial in range(1, max_trials + 1):
        order = int(rng.integers(0, 2))
        test_freq = ref_freq + delta   # test tone is always higher than reference

        print(f"\n[Trial {trial}] delta = {delta:.2f} Hz", end="")
        print(" (playing...)", flush=True)
        play_tones(ref_freq, test_freq, order)

        while True:
            try:
                choice = input("Which tone is higher? (1=first, 2=second): ").strip()
                if choice in ('1', '2'):
                    break
                print("Please enter 1 or 2.")
            except KeyboardInterrupt:
                print("\nTest interrupted.")
                sys.exit(0)

        # Correct judgment logic
        # Determine the actual frequency order of the two tones
        if order == 0:   # first: reference (lower), second: test (higher)
            first_higher = False   # first tone is lower
        else:            # first: test (higher), second: reference (lower)
            first_higher = True    # first tone is higher

        user_choice_higher_first = (choice == '1')
        correct = (user_choice_higher_first == first_higher)

        deltas.append(delta)
        corrects.append(1 if correct else 0)

        if correct:
            print("  Correct")
        else:
            print("  Wrong")

        # Adaptive adjustment
        prev_delta = delta
        if correct:
            delta = max(delta * 0.8, min_delta)
            new_dir = -1
        else:
            delta = min(delta * 1.25, 20.0)
            new_dir = +1

        if trial > 1 and new_dir != direction:
            reversal_count += 1
            reversal_deltas.append(prev_delta)
        direction = new_dir

        print(f"  Next delta: {delta:.2f} Hz  (reversals: {reversal_count})")

        if reversal_count >= n_reversals and delta <= 1.0:
            cont = input("\nEnough reversals obtained. Continue? (y/n): ").strip().lower()
            if cont != 'y':
                break

    return deltas, corrects, reversal_deltas

def main():
    parser = argparse.ArgumentParser(
        description="Pitch discrimination test: measure the minimum frequency difference you can perceive relative to a reference tone",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ref", type=float, default=440.0, help="Reference frequency (Hz), default 440")
    parser.add_argument("--start", type=float, default=5.0, help="Starting frequency delta (Hz), default 5")
    parser.add_argument("--min", type=float, default=0.1, help="Minimum allowed delta (Hz), default 0.1")
    parser.add_argument("--trials", type=int, default=30, help="Maximum number of trials, default 30")
    parser.add_argument("--reversals", type=int, default=6, help="Number of reversals required, default 6")
    args = parser.parse_args()

    print("=" * 60)
    print("Audio Frequency Discrimination Test (Adaptive Staircase)")
    print(f"Reference frequency: {args.ref} Hz")
    print(f"Starting delta: {args.start} Hz")
    print(f"Minimum delta: {args.min} Hz")
    print(f"Maximum trials: {args.trials}")
    print("=" * 60)
    print("Instructions:")
    print("1. Two short tones will play, separated by a brief pause.")
    print("2. Listen carefully and judge whether the **first** or **second** tone is **higher in pitch**.")
    print("3. Press '1' if the first tone is higher, press '2' if the second is higher.")
    input("\nPress Enter to begin...")

    deltas, corrects, reversal_deltas = run_staircase(
        ref_freq=args.ref,
        start_delta=args.start,
        min_delta=args.min,
        max_trials=args.trials,
        n_reversals=args.reversals
    )

    if not deltas:
        print("No valid data collected. Test cancelled.")
        return

    print("\n" + "=" * 60)
    print("Test complete. Analyzing data...")

    if len(reversal_deltas) >= 2:
        n = min(len(reversal_deltas), args.reversals)
        mean_reversal = np.mean(reversal_deltas[-args.reversals:])
        print(f"\n[Reversal method] Mean of last {n} reversal points = {mean_reversal:.2f} Hz")
    else:
        mean_reversal = None
        print("Not enough reversals to estimate threshold via reversal method.")

    threshold_fit = fit_threshold(deltas, corrects)
    if threshold_fit is not None:
        print(f"[Curve fit] Estimated 75% threshold = {threshold_fit:.2f} Hz")
        final_threshold = threshold_fit
    else:
        print("Insufficient data or too much scatter for reliable fit.")
        final_threshold = mean_reversal if mean_reversal is not None else (np.mean(deltas[-5:]) if len(deltas)>=5 else None)

    if final_threshold is not None:
        cents = 1200 * np.log2(1 + final_threshold / args.ref)
        print("\n" + "-" * 60)
        print(f"  Your estimated frequency discrimination threshold: {final_threshold:.2f} Hz")
        print(f"  Equivalent to {cents:.1f} cents")
        print(f"  (relative to {args.ref} Hz)")
    else:
        print("Cannot compute a reliable threshold. Try increasing trials or adjusting parameters.")

    print("\nAccuracy summary by delta range:")
    if len(deltas) > 0:
        bins = np.arange(0, max(deltas)+0.5, 1.0)
        for i in range(len(bins)-1):
            low, high = bins[i], bins[i+1]
            idx = [(low <= d < high) for d in deltas]
            if any(idx):
                acc = np.mean([corrects[j] for j, flag in enumerate(idx) if flag])
                print(f"  F in [{low:.1f}, {high:.1f}) Hz: {acc*100:.0f}% correct")
    print("=" * 60)

if __name__ == "__main__":
    main()
