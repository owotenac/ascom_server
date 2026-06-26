# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI server that controls astronomical telescope mounts via the ASCOM Alpaca protocol. Acts as a bridge between a web/mobile frontend and physical telescope hardware.

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

- **main.py**: FastAPI application entry point. Defines API routes under `/api/v1/mount/` for mount control operations (connect, disconnect, get_position).
- **mount.py**: Telescope control logic using the alpyca library to communicate with ASCOM Alpaca devices. Contains the `Telescope` instance and mount-specific functions.

## Key Dependencies

- **alpyca**: Python client for ASCOM Alpaca protocol - controls telescope mounts over HTTP
- **fastapi/uvicorn**: Web framework and ASGI server

## Hardware Configuration

The mount connection is configured in `mount.py`:
- `URL`: IP address of the ASCOM Alpaca Remote Server (currently `192.168.1.230`)
- `PORT`: Alpaca server port (currently `11111`)

