"""Base entity for the EVA Optic EVAstream integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EvaOpticCoordinator


class EvaOpticEntity(CoordinatorEntity[EvaOpticCoordinator]):
    """Base entity that ties everything to one controller device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EvaOpticCoordinator, key: str) -> None:
        """Initialise with a unique key for this entity type."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="EVAstream",
            manufacturer="EVA Optic",
            model="EVAstream controller",
            configuration_url=f"http://{coordinator.entry.data['host']}",
        )

    @property
    def status(self) -> dict:
        """Shortcut to the latest /status document."""
        return self.coordinator.data or {}
