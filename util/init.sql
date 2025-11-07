CREATE TABLE magnetic_readings (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    ts BIGINT NOT NULL,             
    x DOUBLE PRECISION NOT NULL,
    y DOUBLE PRECISION NOT NULL,
    z DOUBLE PRECISION NOT NULL,
    batch_time BIGINT NOT NULL,     
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT
);

CREATE INDEX idx_magnetic_device_time ON magnetic_readings (device_id, ts);
CREATE INDEX idx_magnetic_batch_time ON magnetic_readings (batch_time);


CREATE TABLE phone_poses (
    id SERIAL PRIMARY KEY,
    device_id TEXT NOT NULL,
    ts BIGINT NOT NULL,             
    pos_x DOUBLE PRECISION,
    pos_y DOUBLE PRECISION,
    pos_z DOUBLE PRECISION,
    ori_x DOUBLE PRECISION,
    ori_y DOUBLE PRECISION,
    ori_z DOUBLE PRECISION,
    ori_w DOUBLE PRECISION,
    batch_time BIGINT NOT NULL,     
    created_at BIGINT NOT NULL DEFAULT (EXTRACT(EPOCH FROM NOW()) * 1000)::BIGINT
);

CREATE INDEX idx_pose_device_time ON phone_poses (device_id, ts);
CREATE INDEX idx_pose_batch_time ON phone_poses (batch_time);