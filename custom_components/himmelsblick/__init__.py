"""Himmelsblick – Wolken in drei Höhen, Aerosole und Staub für Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, KARTE_URL, VERSION
from .coordinator import HimmelsblickCoordinator

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type HimmelsblickConfigEntry = ConfigEntry[HimmelsblickCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Karte ausliefern und im Frontend automatisch laden (keine Ressource nötig)."""
    datei = Path(__file__).parent / "frontend" / "himmelsblick-card.js"
    await hass.http.async_register_static_paths([StaticPathConfig(KARTE_URL, str(datei), False)])
    add_extra_js_url(hass, f"{KARTE_URL}?v={VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HimmelsblickConfigEntry) -> bool:
    """Eintrag einrichten."""
    coordinator = HimmelsblickCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_neu_laden))
    return True


async def _neu_laden(hass: HomeAssistant, entry: HimmelsblickConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: HimmelsblickConfigEntry) -> bool:
    """Eintrag entladen."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
