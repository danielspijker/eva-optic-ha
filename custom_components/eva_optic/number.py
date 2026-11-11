"""Number setpoints for the EVA Optic EVAstream (speed, duration, intensity)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, STREAM_PAUSED, STREAM_RUNNING
from .coordinator import EvaOpticCoordinator
from .entity import EvaOpticEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number setpoints."""
    coordinator: EvaOpticCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            EvaSpeedNumber(coordinator),
            EvaDurationNumber(coordinator),
            EvaTrainingIntensityNumber(coordinator),
        ]
    )


class _EvaStoredNumber(EvaOpticEntity, NumberEntity, RestoreEntity):
    """A setpoint stored in HA and restored across restarts."""

    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator: EvaOpticCoordinator, key: str, default: float
    ) -> None:
        super().__init__(coordinator, key)
        self._value = default

    # Name of the coordinator attribute this setpoint mirrors, if any.
    _coordinator_attr: str | None = None

    async def async_added_to_hass(self) -> None:
        """Restore the last chosen value and sync it to the coordinator."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            try:
                self._value = float(last.state)
            except (TypeError, ValueError):
                pass
        if self._coordinator_attr:
            setattr(self.coordinator, self._coordinator_attr, self._value)

    @property
    def native_value(self) -> float:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = value
        if self._coordinator_attr:
            setattr(self.coordinator, self._coordinator_attr, value)
        self.async_write_ha_state()


class EvaSpeedNumber(_EvaStoredNumber):
    """Free-swim speed. Sent live to the controller while a stream runs."""

    _attr_name = "Vrij zwemmen snelheid"
    _attr_translation_key = "free_speed"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 10
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _coordinator_attr = "free_speed"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "free_speed", 30)

    async def async_set_native_value(self, value: float) -> None:
        await super().async_set_native_value(value)
        stream = (self.status.get("stream") or {}).get("state")
        if stream in (STREAM_RUNNING, STREAM_PAUSED):
            await self.coordinator.client.async_set_speed_gain(int(value))
            await self.coordinator.async_refresh_soon()


class EvaDurationNumber(_EvaStoredNumber):
    """Free-swim duration in minutes, used when starting a session."""

    _attr_name = "Vrij zwemmen duur"
    _attr_translation_key = "free_duration"
    _attr_icon = "mdi:timer"
    _attr_native_min_value = 1
    _attr_native_max_value = 60
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _coordinator_attr = "free_duration"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "free_duration", 10)


class EvaTrainingIntensityNumber(_EvaStoredNumber):
    """Training intensity. Sent live to the controller while a training runs."""

    _attr_name = "Training intensiteit"
    _attr_translation_key = "training_intensity"
    _attr_icon = "mdi:speedometer"
    _attr_native_min_value = 10
    _attr_native_max_value = 100
    _attr_native_step = 5
    _attr_native_unit_of_measurement = PERCENTAGE
    _coordinator_attr = "training_intensity"

    def __init__(self, coordinator: EvaOpticCoordinator) -> None:
        super().__init__(coordinator, "training_intensity", 100)

    async def async_set_native_value(self, value: float) -> None:
        await super().async_set_native_value(value)
        stream = (self.status.get("stream") or {}).get("state")
        if stream in (STREAM_RUNNING, STREAM_PAUSED):
            await self.coordinator.client.async_set_speed_gain(int(value))
            await self.coordinator.async_refresh_soon()
