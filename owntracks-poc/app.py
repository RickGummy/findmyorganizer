"""OwnTracks -> FastAPI -> Leaflet proof of concept.

Run:  uvicorn app:app --host 0.0.0.0 --port 8000
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="OwnTracks PoC")

# Latest location, kept in memory only. Lost on restart.
latest_location: dict | None = None


def _iso(ts: float | int | None) -> str | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


@app.post("/owntracks")
async def owntracks(request: Request):
    global latest_location

    raw = await request.body()
    if not raw.strip():
        print("OwnTracks: empty payload ignored")
        return JSONResponse([])

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print("OwnTracks: non-JSON payload ignored")
        return JSONResponse([])

    if not isinstance(payload, dict):
        print("OwnTracks: non-object payload ignored")
        return JSONResponse([])

    msg_type = payload.get("_type")
    if msg_type != "location":
        print(f"OwnTracks: ignored message _type={msg_type!r}")
        return JSONResponse([])

    lat, lon = payload.get("lat"), payload.get("lon")
    if lat is None or lon is None:
        print("OwnTracks: location payload missing lat/lon, ignored")
        return JSONResponse([])

    received_at = datetime.now(timezone.utc).isoformat()
    first = latest_location is None

    latest_location = {
        "latitude": lat,
        "longitude": lon,
        "timestamp": payload.get("tst"),
        "timestampIso": _iso(payload.get("tst")),
        "accuracy": payload.get("acc"),
        "battery": payload.get("batt"),
        "trigger": payload.get("t"),
        "tid": payload.get("tid"),
        "receivedAt": received_at,
    }

    print("")
    print("OWNTRACKS LOCATION RECEIVED")
    print(f"Latitude: {lat}")
    print(f"Longitude: {lon}")
    print(f"Accuracy: {payload.get('acc')} meters")
    print(f"Phone timestamp: {payload.get('tst')} ({_iso(payload.get('tst'))})")
    print(f"Server received: {received_at}")
    print(f"Battery: {payload.get('batt')}%  Trigger: {payload.get('t')}  Client: {request.client.host if request.client else '?'}")
    if first:
        print("")
        print("REAL IPHONE LOCATION RECEIVED FROM OWNTRACKS")
    print("", flush=True)

    # OwnTracks HTTP mode expects a 200 with a JSON array body.
    return JSONResponse([])


@app.get("/api/location")
def api_location():
    if latest_location is None:
        return {"success": False, "message": "Waiting for location from OwnTracks"}
    return {"success": True, **latest_location}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
