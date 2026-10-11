"""Sensoren für Himmelsblick."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfDensity,
    DEGREE,
    PERCENTAGE,
    UnitOfIrradiance,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import HimmelsblickCoordinator


@dataclass(frozen=True, kw_only=True)
class HimmelSensorBeschreibung(SensorEntityDescription):
    """Beschreibung mit Feld in den Daten."""

    feld: str
    wert: Callable[[Any], Any] | None = None


PROZENT = {"native_unit_of_measurement": PERCENTAGE, "state_class": SensorStateClass.MEASUREMENT}
STRAHL = {
    "native_unit_of_measurement": UnitOfIrradiance.WATTS_PER_SQUARE_METER,
    "device_class": SensorDeviceClass.IRRADIANCE,
    "state_class": SensorStateClass.MEASUREMENT,
}

SENSOREN: tuple[HimmelSensorBeschreibung, ...] = (
    HimmelSensorBeschreibung(key="wolken_gesamt", translation_key="wolken_gesamt", feld="cloud_cover", icon="mdi:cloud", **PROZENT),
    HimmelSensorBeschreibung(key="wolken_hoch", translation_key="wolken_hoch", feld="cloud_cover_high", icon="mdi:weather-cloudy-arrow-right", **PROZENT),
    HimmelSensorBeschreibung(key="wolken_mittel", translation_key="wolken_mittel", feld="cloud_cover_mid", icon="mdi:weather-cloudy", **PROZENT),
    HimmelSensorBeschreibung(key="wolken_tief", translation_key="wolken_tief", feld="cloud_cover_low", icon="mdi:weather-fog", **PROZENT),
    HimmelSensorBeschreibung(key="aerosol", translation_key="aerosol", feld="aerosol_optical_depth", icon="mdi:blur", state_class=SensorStateClass.MEASUREMENT, suggested_display_precision=2),
    HimmelSensorBeschreibung(
        key="staub",
        translation_key="staub",
        feld="dust",
        icon="mdi:weather-dust",
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HimmelSensorBeschreibung(
        key="feinstaub",
        translation_key="feinstaub",
        feld="pm2_5",
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HimmelSensorBeschreibung(key="strahlung", translation_key="strahlung", feld="shortwave_radiation", **STRAHL),
    HimmelSensorBeschreibung(key="strahlung_direkt", translation_key="strahlung_direkt", feld="direct_radiation", **STRAHL),
    HimmelSensorBeschreibung(key="strahlung_diffus", translation_key="strahlung_diffus", feld="diffuse_radiation", **STRAHL),
    HimmelSensorBeschreibung(key="klarer_himmel", translation_key="klarer_himmel", feld="klarer_himmel", icon="mdi:weather-sunny", **STRAHL),
    HimmelSensorBeschreibung(
        key="sonnenhoehe",
        translation_key="sonnenhoehe",
        feld="sonnenhoehe",
        icon="mdi:angle-acute",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Sensoren anlegen."""
    coordinator: HimmelsblickCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [HimmelSensor(coordinator, entry, b) for b in SENSOREN]
    entities.append(HimmelVerlauf(coordinator, entry))
    async_add_entities(entities)


class HimmelBasis(CoordinatorEntity[HimmelsblickCoordinator], SensorEntity):
    """Gemeinsame Basis."""

    _attr_has_entity_name = True
    _attr_attribution = "Daten: Open-Meteo.com (CC BY 4.0)"

    def __init__(self, coordinator: HimmelsblickCoordinator, entry, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Open-Meteo",
            model="Himmelsblick",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
        )


class HimmelSensor(HimmelBasis):
    """Ein aktueller Wert."""

    entity_description: HimmelSensorBeschreibung

    def __init__(self, coordinator, entry, beschreibung: HimmelSensorBeschreibung) -> None:
        super().__init__(coordinator, entry, beschreibung.key)
        self.entity_description = beschreibung

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["aktuell"].get(self.entity_description.feld)


class HimmelVerlauf(HimmelBasis):
    """Tagesverlauf (stündlich) als Attribut – für die Karte."""

    _attr_translation_key = "verlauf"
    _attr_icon = "mdi:chart-timeline-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _unrecorded_attributes = frozenset({"stunden"})

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator, entry, "verlauf")

    @property
    def native_value(self) -> int | None:
        return len(self.coordinator.data["stunden"]) if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if not self.coordinator.data:
            return {}
        return {"stunden": self.coordinator.data["stunden"], "abruf": self.coordinator.data["abruf"]}
