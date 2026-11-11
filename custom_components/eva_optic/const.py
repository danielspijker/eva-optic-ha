"""Constants for the EVA Optic EVAstream integration."""

from __future__ import annotations

DOMAIN = "eva_optic"

# Config
CONF_HOST = "host"
DEFAULT_SCAN_INTERVAL = 15  # seconds

# --- Underwater light cues -------------------------------------------------
# The EVAstream controller drives its multi-colour underwater lighting with
# built-in "cues". Cue 256 switches the lamp off; 257-266 are the fixed
# colours. These are hard-coded in the controller firmware and cannot be read
# back as RGB values, so the integration maps them to friendly names and to a
# representative hex colour for the UI.
CUE_OFF = 256

# Ordered mapping: cue id -> (name, hex colour for the UI swatch)
LIGHT_CUES: dict[int, tuple[str, str]] = {
    257: ("Rood", "#ff0000"),
    258: ("Geel", "#ffff00"),
    259: ("Groen", "#00ff00"),
    260: ("Cyaan", "#00ffff"),
    261: ("Blauw", "#0000ff"),
    262: ("Magenta", "#dd00ff"),
    263: ("Lichtblauw", "#a8ddff"),
    264: ("Wit", "#eeeeee"),
    265: ("Verloop cyaan-blauw", "#00aaff"),
    266: ("Wissel cyaan-blauw", "#00aaff"),
}

# Default colour used when turning the lamp on without a remembered colour.
DEFAULT_CUE = 264  # Wit

# --- Counter-current programs ---------------------------------------------
# Guest user and the program slots as configured on this controller. Each
# training is a program assigned to a slot; its first cue is the "start cue".
# Fitness Training 1-5 -> program 13 (slot 1), cues 30-34
# Sprint Training 1-5  -> program 14 (slot 2), cues 35-39
# Test                 -> program 20 (slot 0), cue 20
GUEST_USER = 4

TRAININGS: dict[str, dict[str, int]] = {
    "Fitness Training 1": {"program": 13, "slot": 1, "start_cue": 0},
    "Fitness Training 2": {"program": 13, "slot": 1, "start_cue": 1},
    "Fitness Training 3": {"program": 13, "slot": 1, "start_cue": 2},
    "Fitness Training 4": {"program": 13, "slot": 1, "start_cue": 3},
    "Fitness Training 5": {"program": 13, "slot": 1, "start_cue": 4},
    "Sprint Training 1": {"program": 14, "slot": 2, "start_cue": 0},
    "Sprint Training 2": {"program": 14, "slot": 2, "start_cue": 1},
    "Sprint Training 3": {"program": 14, "slot": 2, "start_cue": 2},
    "Sprint Training 4": {"program": 14, "slot": 2, "start_cue": 3},
    "Sprint Training 5": {"program": 14, "slot": 2, "start_cue": 4},
    "Test": {"program": 20, "slot": 0, "start_cue": 0},
}

# Stream (counter-current) states as reported by the controller.
STREAM_RUNNING = "running"
STREAM_PAUSED = "paused"
STREAM_STOPPED = "stopped"
STREAM_IDLE = "idle"
