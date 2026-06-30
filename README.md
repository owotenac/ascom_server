# AstroApp

Astrophotography application with telescope control, plate solving, and celestial object catalog.

## Project Structure

```
astro_app/
├── client/astro_app/    # Expo React Native client (web/mobile)
├── server_ascom/        # FastAPI server for ASCOM hardware control
└── build_standalone.bat # Build script for standalone deployment
```

## Development

### Client (Expo)

```bash
cd client/astro_app
npm install
npm run web          # Web development
npm run android      # Android development
npm run ios          # iOS development
```

### Server (FastAPI)

```bash
cd server_ascom
pip install -r requirements.txt
python main.py       # Runs on http://localhost:5001
```

Requires ASCOM Alpaca Remote Server running on the network.

## Standalone Deployment

For deploying on a Windows mini-PC with ASCOM drivers (no dev environment needed):

```bash
# From astro_app root directory
build_standalone.bat
```

This creates a single executable `server_ascom/dist/astro_app.exe` that:
- Serves the web UI at `http://localhost:5001`
- Controls telescope mount and camera via ASCOM
- Performs plate solving via astrometry.net

### Requirements for target machine

- Windows 10/11
- ASCOM Platform + Alpaca Remote Server
- `.env` file with `ASTROMETRY_API_KEY` (place next to exe)

## Features

- Messier/NGC catalog browser with filters
- Sky view with cylindrical projection
- Telescope mount control (connect, slew, track)
- Camera capture with plate solving
- Real-time position display
