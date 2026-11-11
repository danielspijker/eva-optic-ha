"""Async client for the EVA Optic EVAstream controller HTTP API.

The controller exposes an unauthenticated HTTP (not HTTPS) JSON API on the
local network. This client wraps the endpoints that were reverse-engineered
from the controller's own web interface. Everything is local polling; there
is no cloud.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

# The underwater lighting lives on zone 0.
LIGHT_ZONE = 0


class EvaOpticError(Exception):
    """Raised when the controller cannot be reached or returns an error."""


class EvaOpticClient:
    """Minimal async client for one EVAstream controller."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        """Initialise the client for a controller at ``host`` (ip or name)."""
        self._base = f"http://{host}"
        self._session = session

    async def _get(self, path: str) -> dict[str, Any]:
        url = f"{self._base}/{path.lstrip('/')}"
        try:
            async with async_timeout.timeout(10):
                resp = await self._session.get(url)
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise EvaOpticError(f"GET {path} failed: {err}") from err

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> None:
        url = f"{self._base}/{path.lstrip('/')}"
        try:
            async with async_timeout.timeout(10):
                resp = await self._session.post(url, json=payload or {})
                resp.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EvaOpticError(f"POST {path} failed: {err}") from err

    # --- Reads ------------------------------------------------------------
    async def async_get_status(self) -> dict[str, Any]:
        """Return the full /status document."""
        return await self._get("status")

    async def async_get_features(self) -> dict[str, Any]:
        """Return the controller's reported feature set (/features)."""
        return await self._get("features")

    # --- Lighting ---------------------------------------------------------
    async def async_set_cue(self, cue: int, zone: int = LIGHT_ZONE) -> None:
        """Select a light cue (256 = off, 257-266 = colours)."""
        await self._post("start_cue", {"id": cue, "zone": zone})

    async def async_set_intensity(self, intensity: int, zone: int = LIGHT_ZONE) -> None:
        """Set the lamp intensity in percent (0-100)."""
        await self._post("intensity", {"zone": zone, "intensity": intensity})

    # --- Counter-current: free swim --------------------------------------
    async def async_prepare_standalone(self, duration: int, intensity: int) -> None:
        """Prepare a free-swim session. ``duration`` seconds, -1 = unlimited."""
        await self._post("standalone", {"duration": duration, "intensity": intensity})

    async def async_set_paused(self, paused: bool) -> None:
        """Pause (True) or resume/start (False) the prepared/running stream."""
        await self._post("set_paused", {"pause": paused})

    async def async_stop(self) -> None:
        """Stop the running program or free-swim session."""
        await self._post("stop_program")

    async def async_set_speed_gain(self, speed: int) -> None:
        """Change the stream speed live, in percent."""
        await self._post("speed_gain", {"speed_gain": speed})

    async def async_reset_graph(self) -> None:
        """Reset the controller's training graph (used before a training)."""
        await self._post("reset_graph")

    # --- Counter-current: training ---------------------------------------
    async def async_prepare_program(
        self,
        *,
        user: int,
        start_cue: int,
        slot: int,
        program: int,
        speed_gain: int = 100,
    ) -> None:
        """Prepare a training program for a given slot."""
        await self._post(
            "prepare_program",
            {
                "user": user,
                "start_cue": start_cue,
                "slot": slot,
                "program": program,
                "speed_gain": speed_gain,
            },
        )
