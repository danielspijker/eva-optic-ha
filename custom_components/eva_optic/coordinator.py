"""DataUpdateCoordinator for the EVA Optic EVAstream controller."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EvaOpticClient, EvaOpticError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EvaOpticCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /status and exposes it to every entity."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: EvaOpticClient
    ) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.client = client
        self.entry = entry
        # Shared setpoints, written by the number/select entities and read by
        # the buttons. Defaults match the number entities' defaults.
        self.free_speed = 30
        self.free_duration = 10
        self.training_intensity = 100
        self.selected_training = ""

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_status()
        except EvaOpticError as err:
            raise UpdateFailed(str(err)) from err

    async def async_refresh_soon(self) -> None:
        """Request a refresh shortly after a command, so the UI follows fast."""
        await self.async_request_refresh()
