"""
Integration tests for migrate.py, using mongomock to simulate a real
MongoDB instance in-memory (no Docker/network required). Unlike the unit
tests in test_migrate.py, these don't mock individual collection calls :
they exercise migrate_data() end-to-end against a fake but behaviorally
accurate Mongo client, and assert on the resulting documents.
"""

import mongomock
import pandas as pd

import migrate


CSV_HEADER = (
    "Name,Age,Gender,Blood Type,Medical Condition,Date of Admission,"
    "Doctor,Hospital,Insurance Provider,Billing Amount\n"
)


def write_csv(tmp_path, rows):
    csv_path = tmp_path / "healthcare_dataset.csv"
    csv_path.write_text(CSV_HEADER + "\n".join(rows) + "\n")
    return str(csv_path)


def test_migrate_data_end_to_end_with_mongomock(tmp_path, monkeypatch):
    rows = [
        "john doe,40,male,ab+,cancer,2023-05-17,jane roe,city hospital,acme insurance,200.0",
        "mary sue,25,female,o+,flu,2024-02-02,jim beam,other hospital,globex insurance,50.0",
    ]
    csv_path = write_csv(tmp_path, rows)

    fake_client = mongomock.MongoClient()
    monkeypatch.setattr(migrate, "get_db_connection", lambda: fake_client["medical_data"])

    migrate.migrate_data(csv_path)

    collection = fake_client["medical_data"]["admissions"]
    documents = list(collection.find({}))

    assert len(documents) == 2
    names = {doc["Name"] for doc in documents}
    assert names == {"John Doe", "Mary Sue"}

    cancer_doc = collection.find_one({"Name": "John Doe"})
    assert cancer_doc["Medical Condition"] == "Cancer"
    assert cancer_doc["Billing Amount"] == 200.0
    assert cancer_doc["Date of Admission"] == pd.Timestamp("2023-05-17").to_pydatetime()

    index_info = collection.index_information()
    indexed_fields = {
        field
        for name, spec in index_info.items()
        for field, _ in spec["key"]
        if name != "_id_"
    }
    assert indexed_fields == {"Medical Condition", "Hospital", "Date of Admission"}


def test_migrate_data_is_idempotent_on_rerun(tmp_path, monkeypatch):
    rows = ["john doe,40,male,ab+,cancer,2023-05-17,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    fake_client = mongomock.MongoClient()
    monkeypatch.setattr(migrate, "get_db_connection", lambda: fake_client["medical_data"])

    migrate.migrate_data(csv_path)
    migrate.migrate_data(csv_path)

    collection = fake_client["medical_data"]["admissions"]
    assert collection.count_documents({}) == 1
