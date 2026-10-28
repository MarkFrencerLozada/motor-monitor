# Motor Monitor Dashboard

A lightweight Flask web dashboard for industrial motor condition monitoring. It tracks current, winding temperature, and vibration, flags OK / WARN / ALARM status, and estimates minutes to a temperature alarm from the recent trend.

Built by a licensed Electrical Engineer (REE) and marine Electro-Technical Officer. It runs on a phone or tablet under Termux.



![Dashboard](docs/screenshot.png)



## Features

- Live charts: current (A), temperature (C), vibration (mm/s)
- Per-sensor and overall OK / WARN / ALARM status
- Linear-trend estimate of minutes until temperature alarm
- Built-in fault simulator (Inject fault button) for demos
- REST endpoint for feeding real sensor readings

## Run

    pip install -r requirements.txt
    python3 app.py

Open http://localhost:5070

## API

- GET /api/data : latest reading, status, trend, last 60 samples
- POST /api/reading : submit a reading
- POST /api/fault : toggle the simulated fault

Example:

    curl -X POST localhost:5070/api/reading -H "Content-Type: application/json" -d '{"current":18.5,"temp":85,"vib":2.1}'

## Status

Alarm thresholds are currently placeholders (20 A FLA, 110/130 C, 4.5/7.1 mm/s) and must be set from the motor nameplate and applicable standards before real use.

## Roadmap

- [ ] Nameplate-based thresholds with cited standards
- [ ] CSV import / export
- [ ] Modbus input (pymodbus)

## Author

Mark Frencer Lozada, REE | github.com/MarkFrencerLozada
