from fastapi import FastAPI, HTTPException, Depends, Header, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from time import time

from .config import API_KEY
from .db import connect_db, get_db

app = FastAPI(title="Magnetic Collector API", version="0.1.0")

# ---------- Models ----------
class MagneticRecord(BaseModel):
    timestamp: int  # ms since epoch
    x: float
    y: float
    z: float

class UploadPayload(BaseModel):
    device_id: str = Field(..., min_length=1)
    collected_at: Optional[datetime] = None
    records: List[MagneticRecord]

class PoseRecord(BaseModel):
    timestamp: int  # ms since epoch
    pos_x: float = 0
    pos_y: float = 0
    pos_z: float = 0
    ori_x: float = 0
    ori_y: float = 0
    ori_z: float = 0
    ori_w: float = 1

class CombinedUploadPayload(BaseModel):
    device_id: str = Field(..., min_length=1)
    batch_time: Optional[int] = None
    magnetics: List[MagneticRecord] = []
    poses: List[PoseRecord] = []


# ---------- Auth dependency ----------
async def verify_api_key(x_api_key: str = Header(...)):
    # if x_api_key != API_KEY:
    #     raise HTTPException(status_code=401, detail="Invalid API key")
    pass

# ---------- Startup ----------
@app.on_event("startup")
async def on_startup():
    await connect_db()

# ---------- Root ----------
@app.get("/")
def root():
    return {"message": "backend is running"}

# ---------- Routes ----------
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# --------- API Endpoints ----------
from time import time

@app.post("/api/v1/magnetics", dependencies=[Depends(verify_api_key)])
async def upload_magnetics(payload: UploadPayload, db=Depends(get_db)):
    if not payload.records:
        raise HTTPException(status_code=400, detail="records is empty")

    if payload.collected_at:
        if isinstance(payload.collected_at, datetime):
            batch_time_ms = int(payload.collected_at.timestamp() * 1000)
        else:
            batch_time_ms = int(payload.collected_at)
    else:
        batch_time_ms = int(time() * 1000)

    insert_sql = """
        INSERT INTO magnetic_readings
            (device_id, ts, x, y, z, batch_time)
        VALUES ($1, $2, $3, $4, $5, $6)
    """

    rows = []
    for r in payload.records:
        rows.append(
            (
                payload.device_id,
                int(r.timestamp),
                r.x,
                r.y,
                r.z,
                batch_time_ms,
            )
        )

    async with db.acquire() as conn:
        async with conn.transaction():
            for row in rows:
                await conn.execute(insert_sql, *row)

    return {"status": "ok", "inserted": len(rows), "batch_time": batch_time_ms}


@app.get("/api/v1/magnetics/latest", dependencies=[Depends(verify_api_key)])
async def get_latest(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db=Depends(get_db),
):
    sql = """
        SELECT device_id, ts, x, y, z, batch_time, created_at
        FROM magnetic_readings
        WHERE device_id = $1
        ORDER BY ts DESC
        LIMIT $2
    """
    async with db.acquire() as conn:
        rows = await conn.fetch(sql, device_id, limit)

    return [
        {
            "device_id": r["device_id"],
            "timestamp": r["ts"],
            "x": r["x"],
            "y": r["y"],
            "z": r["z"],
            "batch_time": r["batch_time"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]

@app.post("/api/v1/upload", dependencies=[Depends(verify_api_key)])
async def upload(payload: CombinedUploadPayload, db=Depends(get_db)):
    if not payload.magnetics and not payload.poses:
        raise HTTPException(status_code=400, detail="magnetics and poses are both empty")

    if payload.batch_time is not None:
        batch_time_ms = int(payload.batch_time)
    else:
        batch_time_ms = int(time() * 1000) # current time in ms

    insert_magnetic_sql = """
        INSERT INTO magnetic_readings
            (device_id, ts, x, y, z, batch_time)
        VALUES ($1, $2, $3, $4, $5, $6)
    """

    insert_pose_sql = """
        INSERT INTO phone_poses
            (device_id, ts, pos_x, pos_y, pos_z, ori_x, ori_y, ori_z, ori_w, batch_time)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
    """

    async with db.acquire() as conn:
        async with conn.transaction():
            for m in payload.magnetics:
                await conn.execute(
                    insert_magnetic_sql,
                    payload.device_id,
                    int(m.timestamp), 
                    m.x,
                    m.y,
                    m.z,
                    batch_time_ms,
                )

            for p in payload.poses:
                await conn.execute(
                    insert_pose_sql,
                    payload.device_id,
                    int(p.timestamp),  
                    p.pos_x,
                    p.pos_y,
                    p.pos_z,
                    p.ori_x,
                    p.ori_y,
                    p.ori_z,
                    p.ori_w,
                    batch_time_ms,
                )

    return {
        "status": "ok",
        "inserted_magnetics": len(payload.magnetics),
        "inserted_poses": len(payload.poses),
        "batch_time": batch_time_ms,
    }

@app.get("/api/v1/fetch_batch", dependencies=[Depends(verify_api_key)])
async def fetch_batch(
    device_id: str ,
    db=Depends(get_db),
):
    sql = """
        SELECT DISTINCT ON (device_id, batch_time)
            device_id, batch_time
        FROM magnetic_readings
        WHERE device_id = $1
        ORDER BY device_id, batch_time ASC;
    """

    async with db.acquire() as conn:
        rows = await conn.fetch(sql, device_id)
    return [
        {
            "device_id": r["device_id"],
            "batch_time": r["batch_time"],
        }
        for r in rows
    ]


@app.get("/api/v1/fetch", dependencies=[Depends(verify_api_key)])
async def fetch_data(
    device_id: str,
    batch_time: int, 
    db=Depends(get_db),
):
    sql_magnetic = """
        SELECT device_id, ts, x, y, z
        FROM magnetic_readings
        WHERE device_id = $1
          AND batch_time = $2
        ORDER BY ts ASC
    """

    sql_pose = """
        SELECT device_id, ts, pos_x, pos_y, pos_z, ori_x, ori_y, ori_z, ori_w
        FROM phone_poses
        WHERE device_id = $1
          AND batch_time = $2
        ORDER BY ts ASC
    """

    async with db.acquire() as conn:
        magnetics = await conn.fetch(sql_magnetic, device_id, batch_time)
        poses = await conn.fetch(sql_pose, device_id, batch_time)

    return {
        "device_id": device_id,
        "batch_time": batch_time,
        "magnetics": [
            {
                "timestamp": int(r["ts"]),
                "x": r["x"],
                "y": r["y"],
                "z": r["z"],
            }
            for r in magnetics
        ],
        "poses": [
            {
                "timestamp": int(r["ts"]),
                "pos_x": r["pos_x"],
                "pos_y": r["pos_y"],
                "pos_z": r["pos_z"],
                "ori_x": r["ori_x"],
                "ori_y": r["ori_y"],
                "ori_z": r["ori_z"],
                "ori_w": r["ori_w"],
            }
            for r in poses
        ],
    }

@app.get("/api/v1/train", dependencies=[Depends(verify_api_key)])
async def train_model(
    device_id: str,
    batch_time: int,
    model_type: str,
    db=Depends(get_db),
):
    # TODO: Implement training logic here
    return {"status": "training started"}


# @app.post("/api/v1/predict", payload=UploadPayload, dependencies=[Depends(verify_api_key)])
# async def predict(payload: UploadPayload, db=Depends(get_db)):
#     if not payload.records:
#         raise HTTPException(status_code=400, detail="records is empty")

#     # TODO：Implement prediction logic here
#     return {"status": "prediction completed", "predictions": []}

