#!/usr/bin/env python3
import os
import psycopg2
import requests

# ---- config ----
PG_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://maguserydo:magpassydo@localhost:5432/magdb"
)

INFLUX_URL = "http://localhost:8086/write"
INFLUX_DB = "magdata"          # 刚才你建的库
MEASUREMENT = "magnetic"       # measurement 名
BATCH_SIZE = 5000              # 一次写多少行，防止太大


def fetch_magnetic_readings(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT device_id, ts, x, y, z, batch_time
            FROM magnetic_readings
            ORDER BY ts ASC
            """
        )
        rows = cur.fetchall()
    return rows


def line_from_row(row):
    """
    row: (device_id, ts_ms, x, y, z, batch_time_ms)
    Influx line protocol:
    measurement,tag=value field=...,field=... <timestamp>
    我们用 ts_ms，当成 ms，所以写的时候带 precision=ms
    """
    device_id, ts_ms, x, y, z, batch_time_ms = row

    # tag 里不建议有空格
    device_id = device_id.replace(" ", "_")

    line = (
        f"{MEASUREMENT},device_id={device_id} "
        f"x={x},y={y},z={z},batch_time={batch_time_ms} {ts_ms}"
    )
    return line


def write_lines_to_influx(lines):
    if not lines:
        return
    data = "\n".join(lines)
    # precision=ms 因为我们的 ts 是毫秒
    params = {"db": INFLUX_DB, "precision": "ms"}
    resp = requests.post(INFLUX_URL, params=params, data=data)
    resp.raise_for_status()


def main():
    # 1. connect postgres
    conn = psycopg2.connect(PG_DSN)
    print("connected to postgres")

    # 2. fetch rows
    rows = fetch_magnetic_readings(conn)
    print(f"fetched {len(rows)} rows from magnetic_readings")

    # 3. send to influx in batches
    buffer = []
    cnt = 0
    for row in rows:
        line = line_from_row(row)
        buffer.append(line)
        if len(buffer) >= BATCH_SIZE:
            write_lines_to_influx(buffer)
            cnt += len(buffer)
            print(f"written {cnt} lines to influx...")
            buffer = []

    # flush remaining
    if buffer:
        write_lines_to_influx(buffer)
        cnt += len(buffer)
        print(f"written {cnt} lines to influx (final).")

    conn.close()
    print("done.")


if __name__ == "__main__":
    main()
