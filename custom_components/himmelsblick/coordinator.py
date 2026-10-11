"""Datenabruf von Open-Meteo (Wetter + Luftqualität)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
import math
from typing import Any

import aiohttp
from astral import Observer
from astral.sun import elevation

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_INTERVALL, DOMAIN, LUFT, LUFT_URL, STANDARD_INTERVALL, STRAHLUNG, WETTER_URL, WOLKEN

_LOGGER = logging.getLogger(__name__)


def strahlung_klarer_himmel(sonnenhoehe: float) -> float:
    """Globalstrahlung bei wolkenlosem Himmel (Haurwitz-Modell) in W/m²."""
    if sonnenhoehe <= 0:
        return 0.0
    s = math.sin(math.radians(sonnenhoehe))
    return round(1098.0 * s * math.exp(-0.057 / s), 1)


class HimmelsblickCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Holt Wolken in drei Höhen, Strahlung, Aerosole und Staub."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minuten = entry.options.get(CONF_INTERVALL, STANDARD_INTERVALL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=minuten),
        )
        self.lat: float = entry.data[CONF_LATITUDE]
        self.lon: float = entry.data[CONF_LONGITUDE]
        self._ort = Observer(latitude=self.lat, longitude=self.lon)

    async def _hole(self, session: aiohttp.ClientSession, url: str, params: dict) -> dict:
        async with session.get(url, params=params) as antwort:
            antwort.raise_for_status()
            return await antwort.json()

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        basis = {"latitude": self.lat, "longitude": self.lon, "timezone": "auto", "forecast_days": 1}
        try:
            async with asyncio.timeout(30):
                wetter, luft = await asyncio.gather(
                    self._hole(session, WETTER_URL, {**basis, "current": ",".join(WOLKEN + STRAHLUNG), "hourly": ",".join(WOLKEN + STRAHLUNG)}),
                    self._hole(session, LUFT_URL, {**basis, "current": ",".join(LUFT), "hourly": ",".join(LUFT)}),
                )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Open-Meteo nicht erreichbar: {err}") from err
        return self._auswerten(wetter, luft)

    def _hoehe(self, zeit: datetime) -> float:
        return round(elevation(self._ort, zeit), 1)

    def _auswerten(self, wetter: dict, luft: dict) -> dict[str, Any]:
        jetzt = dt_util.now()
        akt_w, akt_l = wetter.get("current", {}), luft.get("current", {})
        hoehe = self._hoehe(jetzt)
        aktuell = {k: akt_w.get(k) for k in WOLKEN + STRAHLUNG} | {k: akt_l.get(k) for k in LUFT}
        aktuell["sonnenhoehe"] = hoehe
        aktuell["klarer_himmel"] = strahlung_klarer_himmel(hoehe)

        stunden: list[dict[str, Any]] = []
        hw, hl = wetter.get("hourly", {}), luft.get("hourly", {})
        luft_index = {t: i for i, t in enumerate(hl.get("time", []))}
        for i, t in enumerate(hw.get("time", [])):
            zeit = dt_util.as_local(datetime.fromisoformat(t).replace(tzinfo=jetzt.tzinfo))
            # Stundenwerte von Open-Meteo gelten für die Stunde davor -> Mitte der Stunde
            mitte = zeit - timedelta(minutes=30)
            j = luft_index.get(t)
            stunden.append(
                {
                    "t": zeit.hour,
                    "tief": hw["cloud_cover_low"][i],
                    "mittel": hw["cloud_cover_mid"][i],
                    "hoch": hw["cloud_cover_high"][i],
                    "ghi": hw["shortwave_radiation"][i],
                    "klar": strahlung_klarer_himmel(self._hoehe(mitte)),
                    "aod": hl["aerosol_optical_depth"][j] if j is not None else None,
                    "staub": hl["dust"][j] if j is not None else None,
                }
            )
        return {"aktuell": aktuell, "stunden": stunden, "abruf": jetzt.isoformat()}
