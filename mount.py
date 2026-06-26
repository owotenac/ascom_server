from alpaca.telescope import *
from alpaca.exceptions import *
from pydantic import BaseModel

URL = "192.168.1.230"
PORT = "11111"


class SlewCoordinates(BaseModel):
    az: float
    alt: float

T: Telescope | None = None


def connect_mount():
    global T
    try:
        if T is not None and T.Connected:
            return {"status": "already_connected", "name": T.Name}

        address = f'{URL}:{PORT}'
        T = Telescope(address, 0)
        T.Connected = True

        return {"status": "connected", "name": T.Name}
    except Exception as e:
        T = None
        return {"status": "error", "message": str(e)}


def disconnect_mount():
    global T
    try:
        if T is None:
            return {"status": "error", "message": "Mount not connected"}

        T.Connected = False
        T = None
        return {"status": "disconnected"}
    except Exception as e:
        T = None
        return {"status": "error", "message": str(e)}


def get_position():
    try:
        if T is None or not T.Connected:
            return {"status": "error", "message": "Mount not connected"}

        return {
            "status": "ok",
            "az": T.Azimuth,
            "alt": T.Altitude
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def state_mount():
    try:
        if T is None or not T.Connected:
            return {"status": "disconnected", "message": "Mount not connected"}

        return {
            "status": "connected",
            "message": "Mount connected"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}        

def slew(coordinates: SlewCoordinates):
    try:
        if T is None or not T.Connected:
            return {"status": "error", "message": "Mount not connected"}

        T.SlewToAltAzAsync(coordinates.az, coordinates.alt)
        return {"status": "slewing", "az": coordinates.az, "alt": coordinates.alt}
    except Exception as e:
        return {"status": "error", "message": str(e)}        