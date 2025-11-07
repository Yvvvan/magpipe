import pandas as pd
import os
from time import time
import asyncio
import asyncpg
from app.config import DATABASE_URL

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "processed")
DATA_PATH = os.path.join(DATA_PATH, "bag_app_record2025-01-28_12-10-30.csv")

DB_URL = DATABASE_URL
DEVICE_ID = "device_12345"

def read_data():
    df = pd.read_csv(DATA_PATH)
    # delete dt_level=0 rows
    df = df[df["dt_level"] != 0]
    df["ts_ms"] = (df["ts"].astype("int64") // 1_000_000)
    return df

async def main():
    df = read_data()
    print(df.head())
    
    # set a batch time
    if len(df) > 0:
        batch_time_ms = int(df["ts_ms"].iloc[0])
    else:
        batch_time_ms = int(time() * 1000)
        
    # connect to db and upload
    conn = await asyncpg.connect(DB_URL)
    
    inserted_magnetic = 0
    inserted_pose = 0
    
    insert_magnetic_sql = """
        INSERT INTO magnetic_readings
            (device_id, ts, x, y, z, batch_time, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """

    insert_pose_sql = """
        INSERT INTO phone_poses
            (device_id, ts,
             pos_x, pos_y, pos_z,
             ori_x, ori_y, ori_z, ori_w,
             batch_time, created_at)
        VALUES ($1, $2,
                $3, $4, $5,
                $6, $7, $8, $9,
                $10, $11)
    """

    async with conn.transaction():
        for _, row in df.iterrows():
            ts_ms = int(row["ts_ms"])
            now_ms = int(time() * 1000)
            

            # 1) MAG：mf_x, mf_y, mf_z
            if {"mf_x", "mf_y", "mf_z"}.issubset(row.index) and not pd.isna(row["mf_x"]):
                # if device_id, ts_ms already exists, skip
                existing = await conn.fetchrow(
                    "SELECT 1 FROM magnetic_readings WHERE device_id=$1 AND ts=$2",
                    DEVICE_ID,
                    ts_ms,
                )
                if not existing:
                    await conn.execute(
                        insert_magnetic_sql,
                        DEVICE_ID,
                        ts_ms,
                    float(row["mf_x"]),
                    float(row["mf_y"]),
                    float(row["mf_z"]),
                    batch_time_ms,
                    now_ms,
                    )
                    inserted_magnetic += 1

            # 2) POS：
            #    dt_lat -> pos_x
            #    dt_lon -> pos_y
            #    dt_level -> pos_z
            #    grv_x.. -> ori_x..
            has_dt = {"dt_lat", "dt_lon", "dt_level"}.issubset(row.index)
            has_grv = {"grv_x", "grv_y", "grv_z", "grv_w"}.issubset(row.index)
            level_val = row["dt_level"] if has_dt else None
            if has_dt and pd.notna(level_val) and float(level_val) != 0.0:
                # if device_id, ts_ms already exists, skip
                existing = await conn.fetchrow(
                    "SELECT 1 FROM phone_poses WHERE device_id=$1 AND ts=$2",
                    DEVICE_ID,
                    ts_ms,
                )
                if not existing:
                    pos_x = float(row["dt_lat"])
                    pos_y = float(row["dt_lon"])
                    pos_z = float(row["dt_level"])

                    # orientation 如果没有就给默认值
                    ori_x = float(row["grv_x"]) if has_grv and not pd.isna(row["grv_x"]) else 0.0
                    ori_y = float(row["grv_y"]) if has_grv and not pd.isna(row["grv_y"]) else 0.0
                    ori_z = float(row["grv_z"]) if has_grv and not pd.isna(row["grv_z"]) else 0.0
                    ori_w = float(row["grv_w"]) if has_grv and not pd.isna(row["grv_w"]) else 1.0

                    await conn.execute(
                        insert_pose_sql,
                        DEVICE_ID,
                        ts_ms,
                        pos_x,
                        pos_y,
                        pos_z,
                        ori_x,
                        ori_y,
                        ori_z,
                        ori_w,
                        batch_time_ms,
                        now_ms,
                    )
                    inserted_pose += 1

    await conn.close()

    print(f"done. magnetic={inserted_magnetic}, poses={inserted_pose}, batch_time={batch_time_ms}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())