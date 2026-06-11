<a id="english-version"></a>
# Healthcare Data ETL Pipeline

*Navigate to: [🇫🇷 Version Française](#version-française)*

## Overview
This project is an automated ETL (Extract, Transform, Load) pipeline. It extracts healthcare patient data from a raw CSV file, cleans and standardizes the data using Python (Pandas), and loads it into a secure, locally-hosted MongoDB database running in a Docker container.

---

## 1. Python Dependencies (`requirements.txt`)
The `requirements.txt` file is used to list all the external Python libraries required for this script to run (such as `pandas`, `pymongo`, and `python-dotenv`). It ensures that any developer working on the project has the exact same environment.

**How to execute it :**
First, it is highly recommended to create and activate a virtual environment. Then, install the dependencies by running the following command in your terminal :
```bash
pip install -r requirements.txt
```

## 2. Environment Variables (`.env`)
The `.env` file is used to securely store sensitive credentials outside of the source code. You must create a `.env` file in the root directory before launching the database or the script.

**Structure :**

`MONGO_ROOT_USERNAME=your_secure_username`  
`MONGO_ROOT_PASSWORD=your_secure_password`

> **Note: Never push your actual `.env` file to version control. It should be added to your `.gitignore`).**

## 3. Database Infrastructure (`docker-compose.yml`)

The `docker-compose.yml` file defines and configures the MongoDB database service. It sets up the container, maps the local port `27017` to the container, reads the `.env` file to create the root user, and establishes a persistent volume so that data is not lost when the container stops.

**How to launch the database :**  
Open your terminal in the project folder and run :
```bash
docker compose up -d
```

To stop the database, use : 
```bash
docker compose stop
```

## 4. Migration Script Description (`migrate.py`)

The `migrate.py` script performs the core ETL operations:

* **Extract :** It reads the raw `healthcare_dataset.csv` using the Pandas library.
* **Transform :**
  * **Missing Values & Whitespace :** Fills empty text fields with "Inconnu" and strips trailing/leading spaces.
  * **Case Normalization :** Applies Title Case to names, hospitals, and doctors; Capitalize for medical conditions and gender; Uppercase for blood types.
  * **Deduplication :** Removes duplicate rows after text normalization.
  * **Type Casting :** Strictly converts Ages to Integers, Billing Amounts to Floats, and string dates to native Python `datetime` objects (handling invalid dates smoothly).
* **Load :** Connects to the local MongoDB instance using the `.env` credentials, clears the existing `admissions` collection to prevent duplication on multiple runs, and performs a bulk insert of all cleaned documents.
* **Indexing :** Creates performance indexes on `Medical Condition`, `Hospital`, and `Date of Admission` to speed up future database queries.

<a id="version-francaise"></a>
# Version Française

*Naviguer vers : [🇬🇧 English Version](#english-version)*

## Vue d'ensemble
Ce projet est un pipeline automatisé d'extraction, de transformation et de chargement. Il extrait des données médicales d'un fichier CSV brut, les nettoie et les standardise à l'aide de Python, puis les charge dans une base de données MongoDB locale et sécurisée fonctionnant sous Docker.

---

## 1. Dépendances Python (`requirements.txt`)
Le fichier `requirements.txt` sert à lister toutes les bibliothèques Python externes nécessaires au bon fonctionnement de ce script. Il garantit que tout développeur reprenant le projet travaillera dans un environnement identique.

**Comment l'exécuter :**
Il est recommandé de créer et d'activer d'abord un environnement virtuel. Ensuite, installez les dépendances en exécutant la commande suivante dans votre terminal :
```bash
pip install -r requirements.txt
```

## 2. Variables d'environnement (`.env`)
Le fichier `.env` permet de stocker vos identifiants sensibles de manière sécurisée, en dehors du code source. Vous devez créer un fichier `.env` à la racine du projet avant de lancer la base de données ou le script.

**Structure :**

`MONGO_ROOT_USERNAME=your_secure_username`  
`MONGO_ROOT_PASSWORD=your_secure_password`

> **Note : Ne publiez jamais votre véritable fichier `.env` sur un gestionnaire de version comme Git. Il doit être ignoré via le fichier `.gitignore`.**

## 3. Infrastructure de la base de données (`docker-compose.yml`)

Le fichier `docker-compose.yml` définit et configure le service de base de données MongoDB. Il paramètre le conteneur, redirige le port `27017` vers votre machine, lit le fichier .env pour créer l'utilisateur administrateur, et met en place un volume persistant pour que les données ne soient pas perdues à l'arrêt du conteneur.

**Comment lancer la base de données :**  
Ouvrez votre terminal dans le dossier du projet et exécutez :
```bash
docker compose up -d
```

Pour arrêter la base de données, utilisez la commande
```bash
docker compose stop
```

## 4. Description et fonctionnement du script (`migrate.py`)

Le script `migrate.py` est le cœur du projet et exécute les opérations suivantes :

* **Extraction :** Il lit le fichier source `healthcare_dataset.csv` en utilisant la bibliothèque Pandas.
* **Transformation :**
  * **Valeurs manquantes et espaces :** Remplit les champs textuels vides par la valeur "Inconnu" et supprime les espaces superflus.
  * **Normalisation de la casse :** Met une majuscule à chaque mot pour les noms propres et les hôpitaux ; une seule majuscule initiale pour les pathologies ; et met tout en majuscule pour les groupes sanguins.
  * **Déduplication :** Supprime les lignes en double après avoir harmonisé le texte.
  * **Typage strict :** Convertit les âges en nombres entiers, les montants facturés en nombres à virgule, et les dates textuelles en objets dates natifs pour permettre des tris chronologiques.
* **Chargement :** Se connecte à l'instance MongoDB locale via les identifiants sécurisés, vide la collection existante pour éviter de multiplier les doublons si le script est relancé, et insère l'intégralité des documents nettoyés en une seule opération.
* **Indexation :** Crée des index de performance sur les champs liés aux pathologies, aux hôpitaux et aux dates d'admission pour accélérer considérablement les futures recherches dans la base de données.