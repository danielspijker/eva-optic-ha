"""Underwater lighting for the EVA Optic EVAstream."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CUE_OFF, DEFAULT_CUE, DOMAIN, LIGHT_CUES
from .coordinator import EvaOpticCoordinator
from .entity import EvaOpticEntity

# name -> cue and the reverse, built once from const.
_NAME_TO_CUE = {name: cue for cue, (name, _hex) in LIGHT_CUES.items()}
_CUE_TO_NAME = {cue: name for cue, (name, _hex) in LIGHT_CUES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the underwater light."""
    coordinator: EvaOpticCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([EvaOpticLight(coordinator)])


class EvaOpticLight(EvaOpticEntity, LightEntity):
    """The multi-colour underwater lighting (zone 0)."""

    _attr_name = "Onderwaterverlichting"
    _attr_translation_key = "underwater"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = list(_NAME_TO_CUE)

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        """Initialise the light and its last-colour memory."""
        super().__init__(coordinator, "underwater")
        self._last_cue = DEFAULT_CUE

    @property
    def _zone(self) -> dict:
        zones = self.status.get("zones") or [{}]
        return zones[0] if zones else {}

    @property
    def _cue(self) -> int:
        return int(self._zone.get("cue", CUE_OFF))

    @property
    def is_on(self) -> bool:
        """The lamp is on for any cue other than 256 (off)."""
        return self._cue != CUE_OFF

    @property
    def brightness(self) -> int | None:
        """0-255 from the controller's 0-100 intensity."""
        intensity = self._zone.get("intensity")
        if intensity is None:
            return None
        return round(int(intensity) * 255 / 100)

    @property
    def effect(self) -> str | None:
        """The active colour name, if the current cue is a known colour."""
        if not self.is_on:
            return None
        return _CUE_TO_NAME.get(self._cue)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on, set a colour and/or set brightness."""
        if (effect := kwargs.get(ATTR_EFFECT)) and effect in _NAME_TO_CUE:
            self._last_cue = _NAME_TO_CUE[effect]
            await self.coordinator.client.async_set_cue(self._last_cue)
        elif not self.is_on:
            # No colour given and lamp is off: use the remembered colour.
            await self.coordinator.client.async_set_cue(self._last_cue)

        if (brightness := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            pct = max(1, round(int(brightness) * 100 / 255))
            await self.coordinator.client.async_set_intensity(pct)

        await self.coordinator.async_refresh_soon()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the lamp off (cue 256)."""
        if self._cue in _CUE_TO_NAME:
            self._last_cue = self._cue
        await self.coordinator.client.async_set_cue(CUE_OFF)
        await self.coordinator.async_refresh_soon()
