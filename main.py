import uvicorn
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from mount import *
from camera import *
from platesolve import solve, solve_status, solve_result
from simu_platesolve import simu_solve, simu_solve_status, simu_solve_result


def get_base_path():
    """Get base path for resources, works with PyInstaller."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(__file__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    return "Ready"


app.add_api_route('/api/v1/mount/connect', connect_mount, methods=['GET'])
app.add_api_route('/api/v1/mount/disconnect', disconnect_mount, methods=['GET'])
app.add_api_route('/api/v1/mount/position', get_position, methods=['GET'])
app.add_api_route('/api/v1/mount/state', state_mount, methods=['GET'])
app.add_api_route('/api/v1/mount/slew', slew, methods=['POST'])

app.add_api_route('/api/v1/camera/connect', connect_camera, methods=['GET'])
app.add_api_route('/api/v1/camera/disconnect', disconnect_camera, methods=['GET'])
app.add_api_route('/api/v1/camera/state', state_camera, methods=['GET'])
app.add_api_route('/api/v1/camera/start_capture', start_capture, methods=['POST'])
app.add_api_route('/api/v1/camera/solve', solve, methods=['POST'])
app.add_api_route('/api/v1/camera/solve_status', solve_status, methods=['POST'])
app.add_api_route('/api/v1/camera/solve_result', solve_result, methods=['POST'])

app.add_api_route('/api/v1/simu/solve', simu_solve, methods=['POST'])
app.add_api_route('/api/v1/simu/solve_status', simu_solve_status, methods=['POST'])
app.add_api_route('/api/v1/simu/solve_result', simu_solve_result, methods=['POST'])

# Mount static files for web client (must be after API routes)
web_dist_path = os.path.join(get_base_path(), "web_dist")
if os.path.exists(web_dist_path):
    app.mount("/", StaticFiles(directory=web_dist_path, html=True), name="static")


def main():
    # Pass app object directly instead of string for PyInstaller compatibility
    uvicorn.run(app, host="0.0.0.0", port=5001)


if __name__ == "__main__":
    main()
