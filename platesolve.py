import os
import json
import requests
from dotenv import load_dotenv
from pydantic import BaseModel

from camera import start_capture, Exposure, FOCAL_LENGTH, C

load_dotenv()

ASTROMETRY_API_URL = "https://nova.astrometry.net/api"
ASTROMETRY_API_KEY = os.getenv("ASTROMETRY_API_KEY")


class AstrometryClient:
    def __init__(self):
        self.session = None

    def login(self) -> bool:
        """Authenticate with astrometry.net and get session token."""
        response = requests.post(
            f"{ASTROMETRY_API_URL}/login",
            data={"request-json": f'{{"apikey": "{ASTROMETRY_API_KEY}"}}'}
        )
        result = response.json()

        if result.get("status") == "success":
            self.session = result.get("session")
            return True
        return False

    def upload(self, fits_path: str, scale_hint: float = None) -> int | None:
        """
        Upload a FITS file to astrometry.net for solving.

        Returns:
            submission_id if successful, None otherwise
        """
        if not self.session:
            return None

        upload_args = {
            "session": self.session,
            "allow_commercial_use": "n",
            "allow_modifications": "n",
            "publicly_visible": "n",
        }

        if scale_hint:
            upload_args["scale_units"] = "arcsecperpix"
            upload_args["scale_est"] = scale_hint
            upload_args["scale_err"] = 20

        with open(fits_path, "rb") as f:
            files = {"file": ("image.fits", f, "application/fits")}
            data = {"request-json": json.dumps(upload_args)}
            response = requests.post(
                f"{ASTROMETRY_API_URL}/upload",
                data=data,
                files=files
            )

        result = response.json()
        if result.get("status") == "success":
            return result.get("subid")
        return None

    def get_submission_status(self, submission_id: int) -> dict:
        """Get submission status and job IDs."""
        response = requests.get(
            f"{ASTROMETRY_API_URL}/submissions/{submission_id}"
        )
        return response.json()

    def get_job_status(self, job_id: int) -> str:
        """Get job status: 'solving', 'success', or 'failure'."""
        response = requests.get(
            f"{ASTROMETRY_API_URL}/jobs/{job_id}"
        )
        result = response.json()
        return result.get("status", "unknown")

    def get_calibration(self, job_id: int) -> dict | None:
        """Get calibration data (RA, Dec, orientation, scale, etc.)"""
        response = requests.get(
            f"{ASTROMETRY_API_URL}/jobs/{job_id}/calibration"
        )
        result = response.json()

        if "ra" in result:
            return {
                "ra": result.get("ra"),
                "dec": result.get("dec"),
                "orientation": result.get("orientation"),
                "pixscale": result.get("pixscale"),
                "radius": result.get("radius"),
                "parity": result.get("parity"),
            }
        return None

    def get_annotations(self, job_id: int) -> list:
        """Get annotations (identified objects in the field)."""
        response = requests.get(
            f"{ASTROMETRY_API_URL}/jobs/{job_id}/annotations",
            headers={"Referer": "https://nova.astrometry.net/api/login"}
        )
        result = response.json()
        return result.get("annotations", [])


# Singleton client instance
_client = AstrometryClient()


def solve(expo: Exposure):
    """
    Capture an image and submit it for plate solving.
    Returns immediately with submission_id - client polls for status.
    """
    capture_result = start_capture(expo)
    if capture_result["status"] != "image_ready":
        return capture_result

    fits_path = capture_result["fits_path"]

    scale_hint = None
    if C is not None and C.Connected:
        scale_hint = (C.PixelSizeX * C.BinX / FOCAL_LENGTH) * 206.265

    if not _client.login():
        return {
            "status": "error",
            "message": "Failed to authenticate with astrometry.net"
        }

    submission_id = _client.upload(fits_path, scale_hint)
    if not submission_id:
        return {
            "status": "error",
            "message": "Failed to upload image to astrometry.net"
        }

    return {
        "status": "submitted",
        "message": "Image submitted for plate solving",
        "submission_id": submission_id
    }


class SubmissionId(BaseModel):
    submission_id: int


class JobId(BaseModel):
    job_id: int


def solve_status(sub: SubmissionId):
    """
    Check the status of a plate solve submission.
    Returns job_id when available, and job status.
    """
    submission_status = _client.get_submission_status(sub.submission_id)

    jobs = submission_status.get("jobs", [])
    job_id = None
    job_status = "pending"

    if jobs and jobs[0] is not None:
        job_id = jobs[0]
        job_status = _client.get_job_status(job_id)

    return {
        "status": "ok",
        "submission_id": sub.submission_id,
        "job_id": job_id,
        "job_status": job_status  # 'pending', 'solving', 'success', 'failure'
    }


def solve_result(job: JobId):
    """
    Get the results of a completed plate solve.
    Call this when job_status is 'success'.
    """
    job_status = _client.get_job_status(job.job_id)

    if job_status != "success":
        return {
            "status": "error",
            "message": f"Job not ready, current status: {job_status}"
        }

    calibration = _client.get_calibration(job.job_id)
    annotations = _client.get_annotations(job.job_id)

    return {
        "status": "solved",
        "job_id": job.job_id,
        "calibration": calibration,
        "annotations": annotations
    }
