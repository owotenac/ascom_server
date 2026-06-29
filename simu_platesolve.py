import os
import base64
from io import BytesIO
from pydantic import BaseModel
from astropy.io import fits
import numpy as np
from PIL import Image

from mock_data import MOCK_CALIBRATION, MOCK_ANNOTATIONS

MOCK_JOB_ID = 99999999


class SimuExposure(BaseModel):
    exposure_time: float
    gain: int


class SimuSubmissionId(BaseModel):
    submission_id: int


class SimuJobId(BaseModel):
    job_id: int


def simu_solve(expo: SimuExposure):
    """
    Simulate plate solving: load test.fits and return immediately with a mock submission_id.
    """
    current_folder = os.getcwd()
    fits_path = os.path.join(current_folder, "test.fits")

    if not os.path.exists(fits_path):
        return {
            "status": "error",
            "message": "test.fits not found"
        }

    with fits.open(fits_path) as hdul:
        nda = hdul[0].data

    # Handle RGB (3, H, W) or grayscale (H, W)
    if nda.ndim == 3:
        nda = np.transpose(nda, (1, 2, 0))  # (3, H, W) -> (H, W, 3)

    img_normalized = ((nda - nda.min()) / (nda.max() - nda.min()) * 255).astype(np.uint8)
    pil_img = Image.fromarray(img_normalized)
    buffer = BytesIO()
    pil_img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return {
        "status": "submitted",
        "message": "Image submitted for plate solving (simulated)",
        "submission_id": MOCK_JOB_ID,
        "image": f"data:image/png;base64,{img_base64}"
    }


def simu_solve_status(sub: SimuSubmissionId):
    """
    Simulate status check: always return success immediately.
    """
    return {
        "submission_id": sub.submission_id,
        "job_id": MOCK_JOB_ID,
        "job_status": "success"
    }


def simu_solve_result(job: SimuJobId):
    """
    Return mock calibration data.
    """
    return {
        "status": "solved",
        "job_id": job.job_id,
        "calibration": MOCK_CALIBRATION,
        "annotations": MOCK_ANNOTATIONS
    }
