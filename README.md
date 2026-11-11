# EVA Optic EVAstream — Home Assistant integration

A custom [Home Assistant](https://www.home-assistant.io/) integration for the
**EVA Optic EVAstream** counter-current swim machine and its multi-colour LED
underwater lighting.

The EVAstream controller has a local web interface but no official Home
Assistant integration. This integration talks to the controller's local HTTP
API directly, so everything runs on your own network with no cloud.

> Not affiliated with or endorsed by EVA Optic. Built by reverse-engineering
> the controller's own web interface on a privately owned unit.

## Features

- **Underwater lighting** as a light entity: on/off, brightness, and the
  controller's fixed colours (red, yellow, green, cyan, blue, magenta, light
  blue, white, and the two cyan-blue gradient/alternating cues) as light
  effects, plus a separate colour select.
- **Counter-current control**:
  - Start a free-swim session with a chosen speed and duration.
  - Pause, resume and stop.
  - Add 5 minutes to a running or paused free-swim session.
  - Start a built-in training program (Fitness 1-5, Sprint 1-5, Test).
  - Change speed/intensity live while swimming.
- **Status sensors**: friendly status (off / running / paused), mode
  (off / free swim / training), remaining time, training duration/elapsed/
  remaining, and the current speed value.

## Requirements

- An EVA Optic EVAstream controller reachable on your LAN over plain HTTP.
- Give the controller a fixed address (a DHCP reservation in your router is the
  simplest), so the integration keeps finding it.

## Installation

### HACS (recommended)

1. In HACS, add this repository as a custom repository (category: *Integration*).
2. Install **EVA Optic EVAstream**.
3. Restart Home Assistant.

### Manual

Copy `custom_components/eva_optic` into your Home Assistant `config/custom_components`
directory and restart Home Assistant.

## Configuration

Settings → Devices & Services → **Add Integration** → *EVA Optic EVAstream*,
then enter the controller's IP address or hostname. All entities are created
automatically under one device.

## The controller API

The integration uses these local HTTP endpoints. Documented here so others can
build on it. All POST bodies are JSON; no authentication is required.

| Method | Path | Body | Purpose |
|--------|------|------|---------|
| GET  | `/status` | — | Full state: `standby`, `speed_gain`, `zones[].cue/intensity`, `stream.state`, `standalone_state`, `standalone_remaining_duration`, `cur_program_cue`, `cur_cue_time`, `simulated_duration`, `stream_speeds[]` |
| GET  | `/features` | — | Feature flags the controller reports |
| POST | `/start_cue` | `{"id": <cue>, "zone": 0}` | Select a light cue. 256 = off, 257-266 = colours |
| POST | `/intensity` | `{"zone": 0, "intensity": <0-100>}` | Set lamp intensity |
| POST | `/standalone` | `{"duration": <sec or -1>, "intensity": <%>}` | Prepare / re-arm a free-swim session |
| POST | `/set_paused` | `{"pause": <bool>}` | Start/resume (false) or pause (true) |
| POST | `/stop_program` | — | Stop the running program or session |
| POST | `/speed_gain` | `{"speed_gain": <%>}` | Change stream speed live |
| POST | `/reset_graph` | — | Reset the training graph (before a training) |
| POST | `/prepare_program` | `{"user", "start_cue", "slot", "program", "speed_gain"}` | Prepare a training program |

### Notes learned from the hardware

- The lamp cannot report its current colour back as RGB; the cue number is all
  you get, so colours are mapped by name.
- During a training the controller drives the lamp itself (colours signal the
  workout phase), so the colour cue is not a user colour at that moment.
- Sending `/standalone` again while a session runs extends it without stopping;
  while paused it keeps the session paused with the new remaining time.
- The controller ignores the `speed_gain` passed to `/prepare_program`, so set
  the intensity with `/speed_gain` once the program is running.

## Disclaimer

Provided as-is under the MIT License. Operating a swim machine from software
carries risk; never start the counter-current when someone may be in or near
the pool. Use at your own risk.
