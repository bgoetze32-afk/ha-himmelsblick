# Himmelsblick

Home-Assistant-Integration (HACS) mit eigener Karte: Wie klar ist der Himmel wirklich?

Daten von [Open-Meteo](https://open-meteo.com) (kostenlos, ohne API-Schlüssel):

- Wolken in drei Höhen – **hohe Wolken (Schleier, z. B. aus Kondensstreifen)**, mittelhohe, tiefe
- **Aerosol-Trübung (AOD)**, Saharastaub, Feinstaub PM2,5
- Globalstrahlung (gesamt, direkt, diffus) und die **Strahlung bei klarem Himmel** (Haurwitz-Modell)

Die Karte `custom:himmelsblick-card` berechnet daraus die **Himmelsklarheit (0–100)** und zeigt die Hauptursache (Schleier, Dunst oder Wolken), den Tagesverlauf und – optional – den Vergleich mit deiner PV-Anlage.

## Installation

1. HACS → Benutzerdefinierte Repositories → dieses Repository als **Integration** hinzufügen → „Himmelsblick“ herunterladen.
2. Home Assistant neu starten.
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Himmelsblick**.

Die Karte wird automatisch geladen, eine Dashboard-Ressource ist nicht nötig.

## Karte

```yaml
type: custom:himmelsblick-card
titel: Himmel
pv: sensor.pv_leistung      # optional, aktuelle PV-Leistung in W
pv_kwp: 8.2                 # optional, installierte Leistung in kWp
kamera: camera.garten       # optional, Himmelsbild
```

## Berechnung der Himmelsklarheit

`Klarheit = 100 × (1 − 0,6 × hoch) × e^−(AOD − 0,05) × (1 − 0,9 × max(mittel, tief))`

Hohe Eiswolken lassen etwa 40 % der Sonne durch, dichte tiefe/mittlere Wolken etwa 10 %; Aerosole werden nach dem Beer-Lambert-Gesetz relativ zu sehr sauberer Luft gerechnet. Ein grober, anschaulicher Index – keine Messung.

Daten: Open-Meteo.com, CC BY 4.0.
