import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()


def get_db_connection():
    """Database connection"""
    username = os.getenv("MONGO_ROOT_USERNAME")
    password = os.getenv("MONGO_ROOT_PASSWORD")

    # Connection string
    uri = f"mongodb://{username}:{password}@localhost:27017/?authSource=admin"
    client = MongoClient(uri)
    return client["medical_data"]

def clean_and_prepare_data(csv_path):
    print(f"Read file : {csv_path}...")

    # Create Dataframe with csv file
    df = pd.read_csv(csv_path)
    # Print the first 5 lines of the dataset
    print(df.head())

    # 1. Trimming & Missing values
    text_columns = ['Name', 'Gender', 'Blood Type', 'Medical Condition', 'Doctor', 'Hospital', 'Insurance Provider']
    for col in text_columns:
        if col in df.columns:
            # Using .loc[:, col] to ensure explicit assignment and prevent chained assignment warnings.
            df.loc[:, col] = df[col].fillna('Inconnu').astype(str).str.strip()

    # 2. Case normalization
    for col in ['Name', 'Doctor', 'Hospital', 'Insurance Provider']:
        if col in df.columns:
            df.loc[:, col] = df[col].str.title()

    for col in ['Gender', 'Medical Condition']:
        if col in df.columns:
            df.loc[:, col] = df[col].str.capitalize()

    if 'Blood Type' in df.columns:
        df.loc[:, 'Blood Type'] = df['Blood Type'].str.upper()

    # 3. Deduplication
    initial_count = len(df)
    df = df.drop_duplicates()
    print(f"Cleaning : {initial_count - len(df)} duplicate lines removed.")

    # 4. AGE : Conversion to INTEGER type, errors become NaN and replaced by 0.
    df.loc[:, 'Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(0).astype(int)

    # 5. BILLING AMOUNT : Conversion to Float/Double, default value 0.0
    df.loc[:, 'Billing Amount'] = pd.to_numeric(df['Billing Amount'], errors='coerce').fillna(0.0).astype(float)

    # 6. DATE OF ADMISSION : Conversion to Datetime. For chronological queries.
    # Invalid dates become NaT (Not a Time), replacing them by a default date
    df.loc[:, 'Date of Admission'] = pd.to_datetime(df['Date of Admission'], errors='coerce')
    # Default date
    default_date = pd.Timestamp('2026-01-01')
    df.loc[:, 'Date of Admission'] = df['Date of Admission'].fillna(default_date)

    # 7. Conversion to dictionaries
    records = df.to_dict(orient='records')

    # 5. Datetime conversion from pandas dates to native Python dates.
    for record in records:
        if pd.notnull(record['Date of Admission']):
            record['Date of Admission'] = record['Date of Admission'].to_pydatetime()

    print(records[0])

    return records

def migrate_data(csv_path):
    """Execute ETL pipeline (Extract, Transform, Load)"""

    # 1. Extract & Transform
    records = clean_and_prepare_data(csv_path)

    if not records:
        print("No data to insert.")
        return

    # 2. Load
    db = get_db_connection()
    # Create collection
    collection = db["admissions"]

    # Optional : Empty the collection to avoid inserting duplicate documents.
    collection.delete_many({})

    # Bulk insert
    result = collection.insert_many(records)
    print(f"Success : {len(result.inserted_ids)} documents inserted in MongoDB.")

    # 3. Indexing
    print("Create indexes...")
    collection.create_index("Medical Condition")
    collection.create_index("Hospital")
    collection.create_index("Date of Admission")
    print("Done")


# Point d'entrée du script (Entry point)
if __name__ == "__main__":
    migrate_data("data/healthcare_dataset.csv")