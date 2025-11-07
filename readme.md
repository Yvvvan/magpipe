# 📘 Magnetic Collector Backend Setup Guide

This guide describes how to run the **Magnetic Collector** backend service in a Python environment, including creating a virtual environment, installing dependencies, initializing the database, and testing the API.

- [📘 Magnetic Collector Backend Setup Guide](#-magnetic-collector-backend-setup-guide)
  - [TO RUN ONLY (Deployment without Docker)](#to-run-only-deployment-without-docker)
  - [TO SETUP (From Scratch)](#to-setup-from-scratch)
    - [1 Setup Python Virtual Environment](#1-setup-python-virtual-environment)
    - [2 Database Configuration (PostgreSQL)](#2-database-configuration-postgresql)
      - [Step 1 Install PostgreSQL](#step-1-install-postgresql)
      - [Step 2 Setup PostgreSQL User and Database](#step-2-setup-postgresql-user-and-database)
      - [Step 3 Initialize Database Schema](#step-3-initialize-database-schema)
      - [Step 4 (Optional) Install Adminer for Database Visualization](#step-4-optional-install-adminer-for-database-visualization)
      - [Step 5 (Optional) Install Grafana for Data Visualization](#step-5-optional-install-grafana-for-data-visualization)
    - [3 Run the Backend Service](#3-run-the-backend-service)
  - [TEST CURL UPLOAD](#test-curl-upload)
    - [1 Upload Sensor Data](#1-upload-sensor-data)
    - [2 Check Uploaded Data](#2-check-uploaded-data)
      - [Option 1: Use psql Command Line](#option-1-use-psql-command-line)
      - [Option 2: Use Adminer Web Interface](#option-2-use-adminer-web-interface)
      - [Option 3: Use the API to fetch latest readings](#option-3-use-the-api-to-fetch-latest-readings)
  - [TEST COLLECTED DATA UPLOAD](#test-collected-data-upload)
  - [TODO Features](#todo-features)
    - [Backend: Server](#backend-server)
    - [Backend: Data](#backend-data)
    - [Backend: Training](#backend-training)
    - [Backend: Test all process](#backend-test-all-process)
    - [Backend: Docker](#backend-docker)
    - [Frontend and Android App](#frontend-and-android-app)


## TO RUN ONLY (Deployment without Docker)

1. make sure postgresql service is started, if not, run:
``` bash
sudo service postgresql start
```

visualaize the database with adminer (optional):
``` bash
cd ./adminer
php -S 0.0.0.0:8080

# then open http://localhost:8080 in browser to login
# use the following credentials:
# System: PostgreSQL
# Server: localhost
# Username: maguserydo
# Password: magpassydo
# Database: magdb
```
visualize the database with grafana (optional):
``` bash
# Start Grafana
sudo service grafana-server start # start in background
# OR
sudo /usr/sbin/grafana-server --homepath=/usr/share/grafana

# Open Grafana in your browser
# Default URL: http://localhost:3000
# Default login: admin/admin

# to solve the port conflict
sudo lsof -i :3000
sudo kill -9 <PID>
```

2. activate virtual env: 
```bash
source .venv/bin/activate
```
run the backend server:
```bash
python -m uvicorn app.main:app --reload

# to test the api, open http://localhost:8000/healthz
# to view the swagger docs, open http://localhost:8000/docs
```


---

## TO SETUP (From Scratch)

### 1 Setup Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

### 2 Database Configuration (PostgreSQL)

#### Step 1 Install PostgreSQL
``` bash
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Start service
sudo service postgresql start
```


#### Step 2 Setup PostgreSQL User and Database
The username, password, database name, host, and port can be customized as needed. 
```bash
# Create user and database
sudo -u postgres psql # open psql shell
```
```sql
CREATE USER maguserydo WITH PASSWORD 'magpassydo';
CREATE DATABASE magdb OWNER maguserydo;
GRANT ALL PRIVILEGES ON DATABASE magdb TO maguserydo;
\q
```
``` bash
# Connection URL: `postgresql://maguserydo:magpassydo@localhost:5432/magdb`
```
And also make a '.env' file in the root directory to store these configurations. This file will be used by the backend service to connect to the database.
```yml
# app config
API_KEY=dev-secret
APP_PORT=8000

# db config
POSTGRES_USER=maguserydo
POSTGRES_PASSWORD=magpassydo
POSTGRES_DB=magdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql://maguserydo:magpassydo@localhost:5432/magdb
```
#### Step 3 Initialize Database Schema

Use `util/init.sql` to initialize the database schema. The database schema includes tables for storing magnetic sensor data and phone position data.

Run the initialization script:
```bash
psql -U maguserydo -h localhost -d magdb -f util/init.sql
```
Verify the table creation:
```bash
psql -U maguserydo -h localhost -d magdb
\dt
```

#### Step 4 (Optional) Install Adminer for Database Visualization

```bash
sudo apt update
sudo apt install -y php php-pgsql

mkdir ./adminer
cd ./adminer
wget https://www.adminer.org/latest.php -O index.php

php -S 0.0.0.0:8080
# then open http://localhost:8080 in browser to login

#####
# May need to change peer authentication to md5 in /etc/postgresql/12/main/pg_hba.conf, change "local all all peer" to "local all all md5". Then restart the service:
sudo service postgresql restart
```

#### Step 5 (Optional) Install Grafana for Data Visualization

```bash
# Install Grafana
sudo apt update
sudo apt install -y grafana

# Start Grafana
sudo service grafana-server start # start in background
# OR
sudo /usr/sbin/grafana-server --homepath=/usr/share/grafana

# Open Grafana in your browser
# Default URL: http://localhost:3000
# Default login: admin/admin
```

---

### 3 Run the Backend Service

```bash
python -m uvicorn app.main:app --reload
```

The backend service will start on `http://127.0.0.1:8000`
- API Docs（Swagger）：`http://127.0.0.1:8000/docs`
- Health Check：`http://127.0.0.1:8000/healthz`

---


## TEST CURL UPLOAD

### 1 Upload Sensor Data
```bash
curl -X POST http://127.0.0.1:8000/api/v1/upload \
  -H "Content-Type: application/json" \
  -H "x-api-key: dev-secret" \
  -d '{
    "device_id": "test_device_01",
    "magnetics": [
      {"timestamp": 1730811000000, "x": 12.3, "y": -5.1, "z": 48.6}
    ],
    "poses": [
      {"timestamp": 1730811000000, "pos_x": 0.5, "pos_y": 1.2, "pos_z": 0.9, "ori_x": 0.0, "ori_y": 0.0, "ori_z": 0.7, "ori_w": 0.7}
    ]
  }'
```

if successful, you should see response:

```json
{"status": "ok", "inserted_magnetics": 1, "inserted_poses": 1, "batch_time": "..."}
```

---

### 2 Check Uploaded Data

#### Option 1: Use psql Command Line
```bash
psql -U maguserydo -h localhost -d magdb
```
```sql
SELECT * FROM magnetic_readings ORDER BY id DESC LIMIT 5;
```
#### Option 2: Use Adminer Web Interface
Open `http://localhost:8080` in your browser, log in with the database credentials, and query the `magnetic_readings` table.

#### Option 3: Use the API to fetch latest readings
```bash
curl -X 'GET' 'http://127.0.0.1:8000/api/v1/magnetics/latest?device_id=test_device_01&limit=5' \
  -H 'accept: application/json' \
  -H 'x-api-key: dev-secret'
```
OR
```bash
# Open in browser:
http://127.0.0.1:8000/docs#
# And run the query there.
```

---
## TEST COLLECTED DATA UPLOAD
Prepare test data and upload to the database.
1. put collected data folder from andriod in `data/collected/` with 3 csv files:
   - DeviceTrajectory.csv (for position)
   - GameRotationVector.csv (for orientation)
   - MagneticField.csv (for magnetic sensor data)
2. run the script to preprocess data to one csv:
```bash
python util/preprocess.py 
```
3. run the script to upload data to database:
```bash
python -m util.upload_data
```
---

## TODO Features

### Backend: Server
- [x] FastAPI backend running on local port 8000

### Backend: Data
- [x] API Key authentication with `x-api-key` header
- [x] Data upload endpoint: `/api/v1/magnetics` (POST)
- [x] Data storage in PostgreSQL database
- [x] Data retrieval endpoint: `/api/v1/magnetics/latest` (GET)
- [x] Swagger UI documentation: `/docs`
- [x] Visualization database with Adminer (table view)
- [x] Visualization dashboard with Grafana
- [ ] Grafana with real-time data

### Backend: Training
- [ ] Backend connection to ML model training service

### Backend: Test all process
- [x] collected data csv to database (static process, using python script)
- [ ] collected data csv to database (real-time process = simulate upload = curl POST each collection)
- [ ] train model with collected data (simulate training)
- [ ] use trained model for real-time prediction (simulate prediction)

### Backend: Docker
- [ ] Dockerfile for backend service  (Permission Lacked, no sudo access to run docker)
  
### Frontend and Android App
- [ ] start collection (upload start)
- [ ] stop collection (upload stop)
- [ ] display collected data in real-time graph
- [ ] group data by collection session and display as a list
- [ ] choose data group to train and display as a trajectory
- [ ] after training, display model performance metrics
- [ ] after training, use the model for real-time prediction


