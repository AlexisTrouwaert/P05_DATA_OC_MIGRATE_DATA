// Executed once, on the very first startup of the mongodb container
// (mounted in /docker-entrypoint-initdb.d). Creates two non-root users,
// scoped to the "medical_data" database only, in addition to the root
// account created by MONGO_INITDB_ROOT_USERNAME/PASSWORD.
//
// - app user      : readWrite  -> used by the migration script (ETL)
// - analyst user  : read only  -> used for data analysis / reporting,
//                    no write access, cannot alter the data

const medicalDb = db.getSiblingDB('medical_data');

medicalDb.createUser({
  user: process.env.MONGO_APP_USERNAME,
  pwd: process.env.MONGO_APP_PASSWORD,
  roles: [
    { role: 'readWrite', db: 'medical_data' }
  ]
});

medicalDb.createUser({
  user: process.env.MONGO_ANALYST_USERNAME,
  pwd: process.env.MONGO_ANALYST_PASSWORD,
  roles: [
    { role: 'read', db: 'medical_data' }
  ]
});
