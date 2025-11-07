"""
This module contains utility functions for preprocessing data.
1. read three csv files from data/collected/xxx, /MagneticField.csv(arrival_ts,event_ts,val_x,val_y,val_z), /DeviceTrajectory.csv(result_ts,pos_ts,lat,lon,level,floor_id,fusion_type,accuracy_meters), /GameRotationVector.csv(arrival_ts,event_ts,val_x,val_y,val_z,val_w)
2. based on the timestamp column, merge the three dataframes into a single dataframe
3. fill missing values using the data with the same timestamp from other rows
4. fill remaining missing values using forward fill method
5. delete rows with any remaining missing values
6. delete rows with duplicate timestamps, keeping the first occurrence
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data", "collected")
DATA_DIR = os.path.join(DATA_DIR, "bag_app_record2025-01-28_12-10-30")  

SAVE_PATH = os.path.join(BASE_DIR, "..", "data", "processed")
SAVE_PATH = os.path.join(SAVE_PATH, "bag_app_record2025-01-28_12-10-30.csv")

def load_and_normalize(base_dir: str):
    
    mf_path = os.path.join(base_dir, "MagneticField.csv")
    dt_path = os.path.join(base_dir, "DeviceTrajectory.csv")
    grv_path = os.path.join(base_dir, "GameRotationVector.csv")

    df_mf = pd.read_csv(mf_path)
    df_dt = pd.read_csv(dt_path)
    df_grv = pd.read_csv(grv_path)

    df_mf = df_mf.rename(columns={
        "event_ts": "ts",
        "val_x": "mf_x",
        "val_y": "mf_y",
        "val_z": "mf_z",
    })

    df_dt = df_dt.rename(columns={
        "result_ts": "ts",
        "lat": "dt_lat",
        "lon": "dt_lon",
        "level": "dt_level",
    })

    df_grv = df_grv.rename(columns={
        "event_ts": "ts",
        "val_x": "grv_x",
        "val_y": "grv_y",
        "val_z": "grv_z",
        "val_w": "grv_w",
    })
    
    df_mf = df_mf[["ts", "mf_x", "mf_y", "mf_z"]]
    df_dt = df_dt[["ts", "dt_lat", "dt_lon", "dt_level"]]
    df_grv = df_grv[["ts", "grv_x", "grv_y", "grv_z", "grv_w"]]

    return df_mf, df_dt, df_grv


def main():
    # read csv
    df_mf, df_dt, df_grv = load_and_normalize(DATA_DIR)
    # merge dataframes on timestamp
    df = df_mf.merge(df_dt, on="ts", how="outer").merge(df_grv, on="ts", how="outer")
    # sort by timestamp
    df = df.sort_values("ts").reset_index(drop=True)
    # fill missing values using data with the same timestamp from other rows
    value_cols = [c for c in df.columns if c != "ts"]
    df[value_cols] = (
        df.groupby("ts")[value_cols]
        .apply(lambda g: g.ffill().bfill())
        .reset_index(level=0, drop=True)
    )
    df = df.sort_values("ts").reset_index(drop=True)
    # forward fill remaining missing values
    df[value_cols] = df[value_cols].ffill()
    # drop rows with any remaining missing values
    df = df.dropna(axis=0, how="any")
    # drop duplicate timestamps, keep first occurrence
    df = df.drop_duplicates(subset=["ts"], keep="first")


    # save to csv
    df.to_csv(SAVE_PATH, index=False)
    print(f"saved to {SAVE_PATH}")



if __name__ == "__main__":
    main()
