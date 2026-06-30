from alpaca.camera import *
from alpaca.exceptions import *
from pydantic import BaseModel
import time
import numpy as np
from astropy.io import fits
import os
import base64
from io import BytesIO
from PIL import Image

URL = "192.168.1.230"
PORT = "11111"
FOCAL_LENGTH = 180  # Chercheur 9x50 ~ 180mm

C: Camera | None = None

def connect_camera():
    global C
    try:
        if C is not None and C.Connected:
            return {"status": "already_connected", "name": C.Name}

        address = f'{URL}:{PORT}'
        C = Camera(address, 0)
        C.Connected = True

        return {"status": "connected", "name": C.Name, "xsize": C.CameraXSize, "ysize": C.CameraYSize}
    except Exception as e:
        C = None
        return {"status": "error", "message": str(e)}


def disconnect_camera():
    global C
    try:
        if C is None:
            return {"status": "error", "message": "Camera not connected"}

        C.Connected = False
        C = None
        return {"status": "disconnected"}
    except Exception as e:
        C = None
        return {"status": "error", "message": str(e)}


def state_camera():
    try:
        if C is None or not C.Connected:
            return {"status": "disconnected", "message": "Camera not connected"}

        return {"status": "connected", "name": C.Name, "xsize": C.CameraXSize, "ysize": C.CameraYSize}

    except Exception as e:
        return {"status": "error", "message": str(e)}    


class Exposure(BaseModel):
    exposure_time: float
    gain: int


def start_capture(expo: Exposure):
    try:
        if C is None or not C.Connected:
            return {"status": "error", "message": "Camera not connected"}

        C.Gain = expo.gain
        C.StartExposure(expo.exposure_time, True)
        
        while not C.ImageReady:
            time.sleep(0.5)
            #print(f'{C.PercentCompleted}% complete')
        print('finished')

        #
        # OK image acquired, grab the image array and the metadata
        #
        img = C.ImageArray
        imginfo = C.ImageArrayInfo
        if imginfo.ImageElementType == ImageArrayElementTypes.Int32:
            if C.MaxADU <= 65535:
                imgDataType = np.uint16
            else:
                imgDataType = np.int32
        elif imginfo.ImageElementType == ImageArrayElementTypes.Double:
            imgDataType = np.float64
        else:
            imgDataType = np.uint16

        #
        # Make a numpy array of he correct shape for astropy.io.fits
        #
        if imginfo.Rank == 2:
            nda = np.array(img, dtype=imgDataType).transpose()
        else:
            nda = np.array(img, dtype=imgDataType).transpose(2,1,0)

        #
        # Now build FITS header and write the file
        #

        header = fits.Header()
        if imginfo.ImageElementType == ImageArrayElementTypes.Int32:
            header['BITPIX'] = 32
            header['BSCALE'] = 1.0
            header['BZERO'] = 0.0
        elif imginfo.ImageElementType == ImageArrayElementTypes.Double:
            header['BITPIX'] = 64
        else:
            header['BITPIX'] = 16
        
        # Add metadata keywords from FITS Image Array Info
        header['CCDAT'] = C.CameraXSize * C.CameraYSize # CCDAT = number of pixels
        header['EXPTIME'] = expo.exposure_time # Exposure Time
        header['GAIN'] = C.Gain # Camera Gain
        #header['DATE-OBS'] = C.LastExposureStartTime
        header['INSTRUME'] = C.SensorName
        header['XBINNING'] = C.BinX
        header['YBINNING'] = C.BinY

        # Pixel size in microns (avec binning)
        header['XPIXSZ'] = C.PixelSizeX * C.BinX
        header['YPIXSZ'] = C.PixelSizeY * C.BinY

        # Focal length in mm
        header['FOCALLEN'] = FOCAL_LENGTH

        # Scale en arcsec/pixel (utile pour plate solving)
        # scale = (pixel_size_um / focal_mm) * 206.265
        header['SCALE'] = (C.PixelSizeX * C.BinX / FOCAL_LENGTH) * 206.265

        header['HISTORY'] = 'Created using Python alpyca-client library'
        header['HISTORY'] = 'OWO'

        currentFolder = os.getcwd()
        
        hdu = fits.PrimaryHDU(nda, header=header)
        fitsFilename = os.path.join(currentFolder, "capture.fits")
        hdu.writeto(fitsFilename, overwrite=True)
        print(f'wrote FITS file {fitsFilename}')

        # Convertir en PNG base64 pour preview
        img_normalized = ((nda - nda.min()) / (nda.max() - nda.min()) * 255).astype(np.uint8)
        pil_img = Image.fromarray(img_normalized)
        buffer = BytesIO()
        pil_img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return {
            "status": "image_ready",
            "message": "Exposure done",
            "image": f"data:image/png;base64,{img_base64}",
            "fits_path": fitsFilename
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

