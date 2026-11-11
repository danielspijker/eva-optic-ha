"""Select entities for the EVA Optic EVAstream (light colour, training)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CUE_OFF, DOMAIN, LIGHT_CUES, TRAININGS
from .coordinator import EvaOpticCoordinator
from .entity import EvaOpticEntity

_NAME_TO_CUE = {name: cue for cue, (name, _hex) in LIGHT_CUES.items()}
_CUE_TO_NAME = {cue: name for cue, (name, _hex) in LIGHT_CUES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the colour and training selects."""
    coordinator: EvaOpticCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [EvaColourSelect(coordinator), EvaTrainingSelect(coordinator)]
    )


class EvaColourSelect(EvaOpticEntity, SelectEntity):
    """Pick the underwater light colour by name."""

    _attr_name = "Lichtkleur"
    _attr_translation_key = "colour"
    _attr_icon = "mdi:palette"
    _attr_options = list(_NAME_TO_CUE)

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        """Initialise the colour select."""
        super().__init__(coordinator, "colour")

    @property
    def current_option(self) -> str | None:
        """The colour currently shown, if the lamp is on a known colour."""
        zones = self.status.get("zones") or [{}]
        cue = int(zones[0].get("cue", CUE_OFF)) if zones else CUE_OFF
        return _CUE_TO_NAME.get(cue)

    async def async_select_option(self, option: str) -> None:
        """Switch the lamp to the chosen colour."""
        if option in _NAME_TO_CUE:
            await self.coordinator.client.async_set_cue(_NAME_TO_CUE[option])
            await self.coordinator.async_refresh_soon()


class EvaTrainingSelect(EvaOpticEntity, SelectEntity):
    """Pick which training the start-training action will run."""

    _attr_name = "Training"
    _attr_translation_key = "training"
    _attr_icon = "mdi:dumbbell"
    _attr_options = list(TRAININGS)

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        """Initialise the training select with a stored choice."""
        super().__init__(coordinator, "training")
        self._selected = next(iter(TRAININGS))
        coordinator.selected_training = self._selected

    @property
    def current_option(self) -> str:
        """The training chosen for the next start (kept in HA, not read back)."""
        return self._selected

    async def async_select_option(self, option: str) -> None:
        """Remember the chosen training, shared with the start-training button."""
        if option in TRAININGS:
            self._selected = option
            self.coordinator.selected_training = option
            self.async_write_ha_state()
