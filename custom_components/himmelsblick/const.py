"""Konstanten für Himmelsblick."""

DOMAIN = "himmelsblick"
VERSION = "0.1.0"

CONF_INTERVALL = "intervall"
STANDARD_INTERVALL = 15  # Minuten

WETTER_URL = "https://api.open-meteo.com/v1/forecast"
LUFT_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WOLKEN = ("cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high")
STRAHLUNG = ("shortwave_radiation", "direct_radiation", "diffuse_radiation")
LUFT = ("aerosol_optical_depth", "dust", "pm2_5")

KARTE_URL = "/himmelsblick/himmelsblick-card.js"
