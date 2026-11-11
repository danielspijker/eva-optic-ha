"""Action buttons for the EVA Optic EVAstream counter-current."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    GUEST_USER,
    STREAM_PAUSED,
    STREAM_RUNNING,
    TRAININGS,
)
from .coordinator import EvaOpticCoordinator
from .entity import EvaOpticEntity

FREE_SWIM_EXTEND_SECONDS = 300


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the counter-current buttons."""
    coordinator: EvaOpticCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            EvaStartFreeSwimButton(coordinator),
            EvaExtendFreeSwimButton(coordinator),
            EvaPauseButton(coordinator),
            EvaResumeButton(coordinator),
            EvaStopButton(coordinator),
            EvaStartTrainingButton(coordinator),
        ]
    )


class _EvaButton(EvaOpticEntity, ButtonEntity):
    """Base button bound to one controller."""


class EvaStartFreeSwimButton(_EvaButton):
    """Start a free-swim session with the stored speed and duration."""

    _attr_name = "Vrij zwemmen starten"
    _attr_translation_key = "start_free_swim"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "start_free_swim")

    async def async_press(self) -> None:
        duration = int(self.coordinator.free_duration) * 60
        intensity = int(self.coordinator.free_speed)
        await self.coordinator.client.async_prepare_standalone(duration, intensity)
        await self.coordinator.client.async_set_paused(False)
        await self.coordinator.async_refresh_soon()


class EvaExtendFreeSwimButton(_EvaButton):
    """Add 5 minutes to a running or paused free-swim session."""

    _attr_name = "Vrij zwemmen +5 minuten"
    _attr_translation_key = "extend_free_swim"
    _attr_icon = "mdi:timer-plus-outline"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "extend_free_swim")

    async def async_press(self) -> None:
        status = self.status
        paused = status.get("standalone_state") == STREAM_PAUSED
        remaining = int(status.get("standalone_remaining_duration", 0) or 0)
        new_duration = remaining + FREE_SWIM_EXTEND_SECONDS
        intensity = int(self.coordinator.free_speed)
        await self.coordinator.client.async_prepare_standalone(new_duration, intensity)
        # async_prepare_standalone leaves a running session running; if it was
        # paused the controller keeps it paused.
        if paused:
            await self.coordinator.client.async_set_paused(True)
        await self.coordinator.async_refresh_soon()


class EvaPauseButton(_EvaButton):
    """Pause the counter-current."""

    _attr_name = "Pauzeren"
    _attr_translation_key = "pause"
    _attr_icon = "mdi:pause"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "pause")

    async def async_press(self) -> None:
        await self.coordinator.client.async_set_paused(True)
        await self.coordinator.async_refresh_soon()


class EvaResumeButton(_EvaButton):
    """Resume a paused counter-current session."""

    _attr_name = "Hervatten"
    _attr_translation_key = "resume"
    _attr_icon = "mdi:play"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "resume")

    async def async_press(self) -> None:
        await self.coordinator.client.async_set_paused(False)
        await self.coordinator.async_refresh_soon()


class EvaStopButton(_EvaButton):
    """Stop the counter-current (any mode)."""

    _attr_name = "Stoppen"
    _attr_translation_key = "stop"
    _attr_icon = "mdi:stop"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "stop")

    async def async_press(self) -> None:
        await self.coordinator.client.async_stop()
        await self.coordinator.async_refresh_soon()


class EvaStartTrainingButton(_EvaButton):
    """Start the training selected on the training select entity."""

    _attr_name = "Training starten"
    _attr_translation_key = "start_training"
    _attr_icon = "mdi:swim"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "start_training")

    async def async_press(self) -> None:
        training = TRAININGS.get(self.coordinator.selected_training)
        if training is None:
            return
        intensity = int(self.coordinator.training_intensity)
        await self.coordinator.client.async_reset_graph()
        await self.coordinator.client.async_prepare_program(
            user=GUEST_USER,
            start_cue=training["start_cue"],
            slot=training["slot"],
            program=training["program"],
            speed_gain=intensity,
        )
        await self.coordinator.client.async_set_paused(False)
        # The controller ignores the intensity sent during prepare, so push it
        # again once the training is running.
        await self.coordinator.client.async_set_speed_gain(intensity)
        await self.coordinator.async_refresh_soon()
