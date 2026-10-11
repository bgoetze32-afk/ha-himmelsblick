"""Einrichtung über die Oberfläche."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_INTERVALL, DOMAIN, STANDARD_INTERVALL


class HimmelsblickConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ort wählen (Standard: Zuhause)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            lat, lon = round(user_input[CONF_LATITUDE], 3), round(user_input[CONF_LONGITUDE], 3)
            await self.async_set_unique_id(f"{lat}_{lon}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={CONF_LATITUDE: lat, CONF_LONGITUDE: lon},
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Himmelsblick"): str,
                vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): cv_float(),
                vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): cv_float(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return HimmelsblickOptionsFlow()


def cv_float() -> selector.NumberSelector:
    return selector.NumberSelector(selector.NumberSelectorConfig(step="any", mode=selector.NumberSelectorMode.BOX))


class HimmelsblickOptionsFlow(OptionsFlow):
    """Abrufintervall einstellen."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        aktuell = self.config_entry.options.get(CONF_INTERVALL, STANDARD_INTERVALL)
        schema = vol.Schema(
            {
                vol.Required(CONF_INTERVALL, default=aktuell): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=5, max=60, step=5, unit_of_measurement="min", mode=selector.NumberSelectorMode.SLIDER)
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
