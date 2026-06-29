# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI server that controls astronomical equipment (telescope mount + camera) via the ASCOM Alpaca protocol. Includes plate solving via astrometry.net. Acts as a bridge between a web/mobile frontend and physical telescope hardware.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server (port 5001, auto-reload enabled)
python main.py
# or directly with uvicorn:
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

## Architecture

- **main.py**: FastAPI application entry point with CORS middleware. Defines API routes:
  - `/api/v1/mount/` - mount control (connect, disconnect, position, state, slew)
  - `/api/v1/camera/` - camera control (connect, disconnect, state, start_capture, solve endpoints)
- **mount.py**: Telescope mount control using alpyca. Functions: connect/disconnect, get_position, state, slew (alt/az async).
- **camera.py**: Camera control using alpyca. Handles image capture, FITS file generation with proper headers (EXPTIME, GAIN, SCALE, FOCALLEN, etc.), and PNG preview encoding.
- **platesolve.py**: Plate solving via astrometry.net API. Client class handles login, upload, status polling, and result retrieval (RA/Dec/orientation/scale).

## Key Dependencies

- **alpyca**: Python client for ASCOM Alpaca protocol - controls telescope/camera over HTTP
- **fastapi/uvicorn**: Web framework and ASGI server
- **astropy**: FITS file handling
- **Pillow**: Image processing for PNG preview
- **requests**: HTTP client for astrometry.net API

## Hardware Configuration

Both mount and camera connections are configured in their respective modules:
- `URL`: IP address of the ASCOM Alpaca Remote Server (currently `192.168.1.230`)
- `PORT`: Alpaca server port (currently `11111`)
- `FOCAL_LENGTH`: Finder scope focal length in mm (currently `180` for 9x50 finder)

## Environment Variables

Create a `.env` file with:
- `ASTROMETRY_API_KEY`: API key for nova.astrometry.net plate solving service

