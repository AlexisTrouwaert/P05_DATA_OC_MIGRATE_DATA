from unittest.mock import MagicMock

import mongomock
import pandas as pd
import pytest

import migrate


CSV_HEADER = (
    "Name,Age,Gender,Blood Type,Medical Condition,Date of Admission,"
    "Doctor,Hospital,Insurance Provider,Billing Amount\n"
)


def write_csv(tmp_path, rows):
    csv_path = tmp_path / "healthcare_dataset.csv"
    csv_path.write_text(CSV_HEADER + "\n".join(rows) + "\n")
    return str(csv_path)


def test_trims_whitespace_and_fills_missing_text_values(tmp_path):
    rows = ['"  bob jones ",30,male,b-,,2024-01-01,"  dr smith",general hospital,,100.5']
    csv_path = write_csv(tmp_path, rows)

    records = migrate.clean_and_prepare_data(csv_path)

    assert len(records) == 1
    record = records[0]
    assert record["Name"] == "Bob Jones"
    assert record["Doctor"] == "Dr Smith"
    # Missing text fields are filled with "Inconnu" before case normalization.
    assert record["Medical Condition"] == "Inconnu"
    assert record["Insurance Provider"] == "Inconnu"


def test_case_normalization_rules_per_column(tmp_path):
    rows = ['john doe,40,male,ab+,cancer,2024-01-01,jane roe,city hospital,acme insurance,200.0']
    csv_path = write_csv(tmp_path, rows)

    record = migrate.clean_and_prepare_data(csv_path)[0]

    assert record["Name"] == "John Doe"           # Title Case
    assert record["Doctor"] == "Jane Roe"          # Title Case
    assert record["Hospital"] == "City Hospital"   # Title Case
    assert record["Insurance Provider"] == "Acme Insurance"  # Title Case
    assert record["Gender"] == "Male"              # Capitalize
    assert record["Medical Condition"] == "Cancer"  # Capitalize
    assert record["Blood Type"] == "AB+"           # Uppercase


def test_duplicate_rows_are_removed_after_normalization(tmp_path):
    rows = [
        "john doe,40,male,ab+,cancer,2024-01-01,jane roe,city hospital,acme insurance,200.0",
        "JOHN DOE,40,MALE,AB+,CANCER,2024-01-01,JANE ROE,CITY HOSPITAL,ACME INSURANCE,200.0",
    ]
    csv_path = write_csv(tmp_path, rows)

    records = migrate.clean_and_prepare_data(csv_path)

    assert len(records) == 1


def test_invalid_age_and_billing_amount_default_to_zero(tmp_path):
    rows = ["john doe,not_a_number,male,ab+,cancer,2024-01-01,jane roe,city hospital,acme insurance,not_a_float"]
    csv_path = write_csv(tmp_path, rows)

    record = migrate.clean_and_prepare_data(csv_path)[0]

    assert record["Age"] == 0
    assert record["Billing Amount"] == 0.0


def test_invalid_admission_date_falls_back_to_default_date(tmp_path):
    rows = ["john doe,40,male,ab+,cancer,not_a_date,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    record = migrate.clean_and_prepare_data(csv_path)[0]

    assert record["Date of Admission"] == pd.Timestamp("2026-01-01").to_pydatetime()


def test_valid_admission_date_is_parsed_and_kept(tmp_path):
    rows = ["john doe,40,male,ab+,cancer,2023-05-17,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    record = migrate.clean_and_prepare_data(csv_path)[0]

    assert record["Date of Admission"] == pd.Timestamp("2023-05-17").to_pydatetime()


def test_missing_optional_text_column_does_not_crash(tmp_path):
    # No "Doctor" column at all in the source CSV.
    header = (
        "Name,Age,Gender,Blood Type,Medical Condition,Date of Admission,"
        "Hospital,Insurance Provider,Billing Amount\n"
    )
    row = "john doe,40,male,ab+,cancer,2023-05-17,city hospital,acme insurance,200.0\n"
    csv_path = tmp_path / "healthcare_dataset.csv"
    csv_path.write_text(header + row)

    record = migrate.clean_and_prepare_data(str(csv_path))[0]

    assert "Doctor" not in record
    assert record["Hospital"] == "City Hospital"


def test_non_consecutive_duplicates_are_removed(tmp_path):
    rows = [
        "john doe,40,male,ab+,cancer,2024-01-01,jane roe,city hospital,acme insurance,200.0",
        "mary sue,25,female,o+,flu,2024-02-02,jim beam,other hospital,globex insurance,50.0",
        "JOHN DOE,40,MALE,AB+,CANCER,2024-01-01,JANE ROE,CITY HOSPITAL,ACME INSURANCE,200.0",
    ]
    csv_path = write_csv(tmp_path, rows)

    records = migrate.clean_and_prepare_data(csv_path)

    assert len(records) == 2
    names = {record["Name"] for record in records}
    assert names == {"John Doe", "Mary Sue"}


def test_negative_age_is_kept_as_is(tmp_path):
    rows = ["john doe,-5,male,ab+,cancer,2024-01-01,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    record = migrate.clean_and_prepare_data(csv_path)[0]

    # Documents current behavior: negative ages are numeric, so they are not
    # coerced to 0 like genuinely invalid (non-numeric) values would be.
    assert record["Age"] == -5


def test_get_db_connection_defaults_to_localhost_when_mongo_host_unset(monkeypatch):
    monkeypatch.setenv("MONGO_APP_USERNAME", "app_user")
    monkeypatch.setenv("MONGO_APP_PASSWORD", "secret")
    monkeypatch.delenv("MONGO_HOST", raising=False)

    captured_uri = {}

    class FakeMongoClient:
        def __init__(self, uri):
            captured_uri["uri"] = uri

        def __getitem__(self, name):
            return name

    monkeypatch.setattr(migrate, "MongoClient", FakeMongoClient)

    migrate.get_db_connection()

    assert captured_uri["uri"] == "mongodb://app_user:secret@localhost:27017/?authSource=medical_data"


def test_empty_csv_returns_no_records_without_crashing(tmp_path):
    csv_path = tmp_path / "healthcare_dataset.csv"
    csv_path.write_text(CSV_HEADER)

    records = migrate.clean_and_prepare_data(str(csv_path))

    assert records == []


def test_migrate_data_skips_load_when_no_records(tmp_path, monkeypatch):
    csv_path = tmp_path / "healthcare_dataset.csv"
    csv_path.write_text(CSV_HEADER)

    get_db_connection_mock = MagicMock()
    monkeypatch.setattr(migrate, "get_db_connection", get_db_connection_mock)

    migrate.migrate_data(str(csv_path))

    get_db_connection_mock.assert_not_called()


def test_migrate_data_clears_collection_then_bulk_inserts(tmp_path, monkeypatch):
    rows = ["john doe,40,male,ab+,cancer,2023-05-17,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    fake_collection = MagicMock()
    fake_collection.insert_many.return_value = MagicMock(inserted_ids=["id1"])
    fake_db = {"admissions": fake_collection}
    monkeypatch.setattr(migrate, "get_db_connection", lambda: fake_db)

    migrate.migrate_data(csv_path)

    fake_collection.delete_many.assert_called_once_with({})
    assert fake_collection.insert_many.call_count == 1
    inserted_records = fake_collection.insert_many.call_args[0][0]
    assert len(inserted_records) == 1
    assert inserted_records[0]["Name"] == "John Doe"


def test_migrate_data_creates_expected_indexes(tmp_path, monkeypatch):
    rows = ["john doe,40,male,ab+,cancer,2023-05-17,jane roe,city hospital,acme insurance,200.0"]
    csv_path = write_csv(tmp_path, rows)

    fake_collection = MagicMock()
    fake_collection.insert_many.return_value = MagicMock(inserted_ids=["id1"])
    fake_db = {"admissions": fake_collection}
    monkeypatch.setattr(migrate, "get_db_connection", lambda: fake_db)

    migrate.migrate_data(csv_path)

    indexed_fields = {call.args[0] for call in fake_collection.create_index.call_args_list}
    assert indexed_fields == {"Medical Condition", "Hospital", "Date of Admission"}


def test_get_db_connection_uses_app_credentials_and_mongo_host(monkeypatch):
    monkeypatch.setenv("MONGO_APP_USERNAME", "app_user")
    monkeypatch.setenv("MONGO_APP_PASSWORD", "secret")
    monkeypatch.setenv("MONGO_HOST", "mongodb")

    captured_uri = {}

    class FakeMongoClient:
        def __init__(self, uri):
            captured_uri["uri"] = uri

        def __getitem__(self, name):
            return name

    monkeypatch.setattr(migrate, "MongoClient", FakeMongoClient)

    db_name = migrate.get_db_connection()

    assert db_name == "medical_data"
    assert captured_uri["uri"] == "mongodb://app_user:secret@mongodb:27017/?authSource=medical_data"
