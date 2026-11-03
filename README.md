# 🚖 Uber Data Engineering ETL Pipeline (GCP, Mage AI & BigQuery)

## 📖 Project Overview

This is an end-to-end cloud-based Data Engineering and Analytics project built using Google Cloud Platform (GCP), Mage AI, Python, and Google BigQuery.

The main objective of this project is to extract raw Uber trip data, organize it into a structured Star Schema, and prepare an analytics-ready dataset for Business Intelligence (BI) reporting using Looker Studio.

The project demonstrates a complete data workflow, from cloud infrastructure setup and data ingestion to data transformation, warehouse modeling, and dashboard development.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Cloud Platform | Google Cloud Platform (GCP) |
| Cloud Infrastructure | Google Compute Engine VM |
| Operating System | Debian Linux |
| Data Lake / Storage | Google Cloud Storage (GCS) |
| Orchestration & ETL | Mage AI |
| Programming Language | Python |
| Python Libraries | Pandas, Requests |
| Data Warehouse | Google BigQuery |
| Query Language | SQL |
| Data Modeling | Star Schema, Lucidchart |
| Data Visualization | Looker Studio |

---

## 🏗️ Project Architecture

The project follows an end-to-end data engineering workflow:

1. Uber CSV data is stored in Google Cloud Storage.
2. A Google Cloud Compute Engine VM is configured with Python and Mage AI.
3. Mage AI is used to build the ETL workflow.
4. Raw Uber data is loaded into Google BigQuery.
5. The data is organized into one fact table and seven dimension tables.
6. SQL JOIN operations combine the tables into a final analytics table.
7. BigQuery data is connected to Looker Studio for visualization and reporting.

### Architecture Flow

```text
        Uber Raw CSV Dataset
                 |
                 v
       Google Cloud Storage
                 |
                 v
      Google Compute Engine VM
                 |
                 v
              Mage AI
        (ETL Pipeline Setup)
                 |
                 v
       Data Extraction & Loading
                 |
                 v
          Google BigQuery
                 |
                 v
       Raw Data / Staging Table
                 |
                 v
        Data Transformation
                 |
                 v
       Star Schema Data Model
                 |
          +------+------+
          |             |
          v             v
      Fact Table    Dimension Tables
                    (7 Tables)
          |             |
          +------+------+
                 |
                 v
          SQL JOIN Operations
                 |
                 v
          tbl_analytics
                 |
                 v
          Looker Studio
                 |
                 v
       Interactive Dashboards
          & BI Reports
```

---

## ☁️ 1. Google Cloud Platform Setup

The project infrastructure was configured on Google Cloud Platform.

### Activities Performed

- Created a Google Cloud project.
- Configured a Compute Engine Virtual Machine.
- Used Debian Linux as the operating system.
- Installed and configured Python.
- Created a Python virtual environment.
- Installed Mage AI and its required dependencies.
- Prepared the cloud environment for running the ETL workflow.

Python 3.11 was used in a virtual environment to ensure compatibility with Mage AI.

---

## 📥 2. Data Extraction – Mage AI

The raw Uber dataset was hosted on Google Cloud Storage.

Mage AI was configured to retrieve the CSV file from the GCS URL using Python Requests and load it into a Pandas DataFrame.

### Source Dataset

- **Source:** Google Cloud Storage
- **File:** `uber_data.csv`
- **Total Records:** 100,000
- **Total Columns:** 19

### Extraction Code

```python
import io
import pandas as pd
import requests

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(*args, **kwargs):
    url = 'https://storage.googleapis.com/uber-data-engineer-sonu/uber_data.csv'

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    df = pd.read_csv(io.BytesIO(response.content))

    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    return df
```

The extraction process successfully retrieved 100,000 rows and 19 columns from the source dataset.

---

## 🔄 3. Data Transformation – Star Schema

The raw Uber dataset contains trip details, passenger information, timestamps, locations, payment details, and fare metrics.

To organize this data for analytical queries, a Star Schema data model was designed.

The data was divided into:

- One Fact Table
- Seven Dimension Tables

### ⭐ Fact Table

**Table Name:** `fact_table`

The fact table stores trip-level transactional information and foreign keys connecting the dimension tables.

Important columns include:

- `VendorID`
- `datetime_id`
- `passenger_count_id`
- `trip_distance_id`
- `rate_code_id`
- `pickup_location_id`
- `dropoff_location_id`
- `payment_type_id`
- `fare_amount`
- `tip_amount`
- `tolls_amount`
- `total_amount`

### 📌 Dimension Tables

| Dimension Table | Description |
|---|---|
| `datetime_dim` | Pickup and dropoff timestamps, hour, day, month, year, and weekday |
| `passenger_count_dim` | Passenger count information |
| `trip_distance_dim` | Trip distance information |
| `rate_code_dim` | Rate codes and their descriptions |
| `pickup_location_dim` | Pickup latitude and longitude |
| `dropoff_location_dim` | Dropoff latitude and longitude |
| `payment_type_dim` | Payment types and their descriptions |

### Data Modeling Diagram

The Star Schema was designed to organize transactional data and descriptive attributes into related tables.

![Uber Star Schema](./Data_Modelling/Data%20Modelling%202.png)

*Final Star Schema data model.*

---

## 🏢 4. Data Warehouse – Google BigQuery

Google BigQuery was used as the cloud data warehouse.

The original Uber CSV dataset was uploaded into the following table:

```text
uber-513106.uber_data_engineering.uber_raw_data
```

After loading the raw dataset, SQL transformations were performed to create the fact and dimension tables.

### BigQuery Dataset Structure

```text
uber_data_engineering
│
├── uber_raw_data
│
├── fact_table
│
├── datetime_dim
├── passenger_count_dim
├── trip_distance_dim
├── rate_code_dim
├── pickup_location_dim
├── dropoff_location_dim
└── payment_type_dim
```

This structure keeps the original raw data separate from the transformed analytical tables.

---

## 🔗 5. SQL Transformation – Final Analytics Table

After creating the fact and dimension tables, SQL JOIN operations were used to combine their information.

A final analytics table named `tbl_analytics` was created in BigQuery.

### SQL Query

```sql
CREATE OR REPLACE TABLE
`uber-513106.uber_data_engineering.tbl_analytics` AS

SELECT
    f.VendorID,
    d.tpep_pickup_datetime,
    d.tpep_dropoff_datetime,
    p.passenger_count,
    t.trip_distance,
    r.rate_code_name,
    pick.pickup_latitude,
    pick.pickup_longitude,
    dr.dropoff_latitude,
    dr.dropoff_longitude,
    pay.payment_type_name,
    f.fare_amount,
    f.extra,
    f.mta_tax,
    f.tip_amount,
    f.tolls_amount,
    f.improvement_surcharge,
    f.total_amount

FROM
`uber-513106.uber_data_engineering.fact_table` f

JOIN
`uber-513106.uber_data_engineering.datetime_dim` d
ON f.datetime_id = d.datetime_id

JOIN
`uber-513106.uber_data_engineering.passenger_count_dim` p
ON p.passenger_count_id = f.passenger_count_id

JOIN
`uber-513106.uber_data_engineering.trip_distance_dim` t
ON t.trip_distance_id = f.trip_distance_id

JOIN
`uber-513106.uber_data_engineering.rate_code_dim` r
ON r.rate_code_id = f.rate_code_id

JOIN
`uber-513106.uber_data_engineering.pickup_location_dim` pick
ON pick.pickup_location_id = f.pickup_location_id

JOIN
`uber-513106.uber_data_engineering.dropoff_location_dim` dr
ON dr.dropoff_location_id = f.dropoff_location_id

JOIN
`uber-513106.uber_data_engineering.payment_type_dim` pay
ON pay.payment_type_id = f.payment_type_id;
```

### Purpose of the Final Table

The `tbl_analytics` table contains the required trip details, passenger information, timestamps, locations, payment descriptions, and fare metrics in a single analytical dataset.

This table acts as the primary source for the final BI reports.

---

## 📊 6. Data Visualization – Looker Studio

After preparing the final analytics table in BigQuery, the data was connected to Looker Studio to build visual reports.

### Activities Performed

- Connected Google BigQuery as the data source.
- Used the final `tbl_analytics` table.
- Created visual charts and reports.
- Presented Uber trip information in an analytical format.
- Prepared dashboards for business intelligence and reporting.

The visualizations help explore trip patterns, passenger trends, distance information, payment types, and fare metrics.

### Final Dashboard

**[View Uber Analytics Dashboard](./Dashboard/Uber_Dashboard.pdf)**

---

## 📂 7. Project Folder Structure

```text
uber-data-engineering/
│
├── README.md
│
├── Dashboard/
│   └── Uber_Dashboard.pdf
│
├── Data/
│   └── sample_uber_data.csv
│
├── Data_Modelling/
│   ├── Data Modelling 1.png
│   └── Data Modelling 2.png
│
├── mage-files/
│   ├── extract.py
│   ├── transform.py
│   └── load.py
│
└── Pipeline/
    └── uber-etl-pipeline/
```

---

## 🎯 8. Key Learning Outcomes

Through this project, I gained practical experience in:

- Setting up cloud infrastructure using Google Cloud Platform.
- Working with Linux-based virtual machines.
- Configuring Python environments and dependencies.
- Understanding ETL concepts: Extraction, Transformation, and Loading.
- Building data workflows using Mage AI.
- Loading and managing data in Google BigQuery.
- Designing a Star Schema using fact and dimension tables.
- Writing SQL queries and performing multi-table JOIN operations.
- Creating analytics-ready datasets.
- Connecting cloud data warehouses to Looker Studio.
- Building BI reports and visualizations.

---

## 👨‍💻 Author

**Sonu Kumar Thakur**

Data Engineering | Data Analytics

New Delhi, India

**GitHub:** [github.com/sonukrthakur3](https://github.com/sonukrthakur3)
