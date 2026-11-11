"""Sensors for the EVA Optic EVAstream."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    STREAM_PAUSED,
    STREAM_RUNNING,
)
from .coordinator import EvaOpticCoordinator
from .entity import EvaOpticEntity


def _stream_state(status: dict[str, Any]) -> str:
    return (status.get("stream") or {}).get("state", "stopped")


def _is_free_swim(status: dict[str, Any]) -> bool:
    """A free-swim session is active when standalone is running/paused."""
    return status.get("standalone_state") in (STREAM_RUNNING, STREAM_PAUSED) or int(
        status.get("standalone_remaining_duration", 0) or 0
    ) > 0


def _status_text(status: dict[str, Any]) -> str:
    state = _stream_state(status)
    if state == STREAM_PAUSED or status.get("standalone_state") == STREAM_PAUSED:
        return "Gepauzeerd"
    if state == STREAM_RUNNING:
        return "Draait"
    if state in ("stopped", "idle"):
        return "Uit"
    return state


def _mode_text(status: dict[str, Any]) -> str:
    if _stream_state(status) not in (STREAM_RUNNING, STREAM_PAUSED):
        return "uit"
    return "vrij" if _is_free_swim(status) else "training"


def _free_remaining(status: dict[str, Any]) -> int:
    return int(status.get("standalone_remaining_duration", 0) or 0)


def _training_total(status: dict[str, Any]) -> int:
    # simulated_duration is in milliseconds.
    return round(int(status.get("simulated_duration", 0) or 0) / 1000)


def _training_elapsed(status: dict[str, Any]) -> int:
    # cur_cue_time is in milliseconds.
    return round(int(status.get("cur_cue_time", 0) or 0) / 1000)


def _training_remaining(status: dict[str, Any]) -> int:
    return max(0, _training_total(status) - _training_elapsed(status))


@dataclass(frozen=True, kw_only=True)
class EvaSensorDescription(SensorEntityDescription):
    """Describes an EVA sensor and how to read its value from /status."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[EvaSensorDescription, ...] = (
    EvaSensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:waves",
        value_fn=_status_text,
    ),
    EvaSensorDescription(
        key="mode",
        translation_key="mode",
        icon="mdi:swim",
        value_fn=_mode_text,
    ),
    EvaSensorDescription(
        key="free_remaining",
        translation_key="free_remaining",
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=_free_remaining,
    ),
    EvaSensorDescription(
        key="training_total",
        translation_key="training_total",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=_training_total,
    ),
    EvaSensorDescription(
        key="training_elapsed",
        translation_key="training_elapsed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=_training_elapsed,
    ),
    EvaSensorDescription(
        key="training_remaining",
        translation_key="training_remaining",
        icon="mdi:timer-sand",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=_training_remaining,
    ),
    EvaSensorDescription(
        key="speed_gain",
        translation_key="speed_gain",
        icon="mdi:speedometer",
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda s: int(s.get("speed_gain", 0) or 0),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EVA sensors."""
    coordinator: EvaOpticCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EvaOpticSensor(coordinator, description) for description in SENSORS
    )


class EvaOpticSensor(EvaOpticEntity, SensorEntity):
    """A single read-only value derived from /status."""

    entity_description: EvaSensorDescription

    def __init__(
        self, coordinator: EvaOpticCoordinator, description: EvaSensorDescription
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        """Return the value computed from the latest status."""
        return self.entity_description.value_fn(self.status)
