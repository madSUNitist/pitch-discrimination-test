# Pitch Discrimination Test

A psychoacoustic test that measures your minimum perceivable frequency difference around a reference tone (default 440 Hz) using an adaptive staircase procedure.

## Requirements

- Python 3.13+
- A working audio output device

## Installation

```bash
# Clone and enter the project
git clone git@github.com:madSUNitist/pitch-discrimination-test.git
cd pitch-discrimination-test

# Install with uv (recommended)
uv sync
```

## Usage

Activate the virtual environment or use `uv run`:

```bash
# Option A: activate venv, then run directly
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux / macOS
python main.py

# Option B: run via uv (no activation needed)
uv run main.py
```

When passing arguments through `uv run`, use `--` to separate uv options from script arguments:

```bash
uv run main.py -- --ref 500 --start 10 --trials 40
```

Or `uv run` the interpreter directly:

```bash
uv run python main.py --ref 500 --start 10 --trials 40
```

### Example

```bash
# Use 500 Hz reference, start with 10 Hz delta, up to 40 trials
python main.py --ref 500 --start 10 --trials 40
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--ref` | 440.0 | Reference frequency in Hz |
| `--start` | 5.0 | Starting frequency delta in Hz |
| `--min` | 0.1 | Minimum allowed delta in Hz |
| `--trials` | 30 | Maximum number of trials |
| `--reversals` | 6 | Number of reversals required |

## How It Works

1. Two short pure tones (0.8 s each) are played with a 0.4 s silence between them.
2. One tone is the reference frequency; the other is slightly higher (reference + delta).
3. You indicate which tone sounds higher in pitch.
4. The delta adapts: it shrinks after correct answers and grows after mistakes.
5. The test ends after enough reversals (direction changes) are recorded, or when the maximum trial count is reached.
6. Results are reported in Hz and cents via both reversal averaging and psychometric curve fitting.

## Output

The test reports:
- **Reversal method**: mean of the last N reversal deltas
- **Curve fit**: 75% correct threshold estimated from a psychometric function
- **Accuracy summary**: correctness rate broken down by delta ranges
