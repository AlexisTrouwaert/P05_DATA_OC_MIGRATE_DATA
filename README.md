<a id="english-version"></a>
# Healthcare Data ETL Pipeline

*Navigate to: [🇫🇷 Version Française](#version-française)*

## Overview
This project is an automated ETL (Extract, Transform, Load) pipeline. It extracts healthcare patient data from a raw CSV file, cleans and standardizes the data using Python (Pandas), and loads it into a secure, locally-hosted MongoDB database running in a Docker container.

---

## 1. Python Dependencies (`requirements.txt`)
The `requirements.txt` file lists all the external Python libraries required for this script to run (`pandas`, `pymongo`, `python-dotenv`, `pytest`). When you use Docker (recommended, see section 3), these dependencies are installed **automatically** during the image build — you don't need to install anything manually.

**Manual installation (only if you want to run `migrate.py` outside Docker) :**
First, create and activate a virtual environment. Then, install the dependencies by running the following command in your terminal :
```bash
pip install -r requirements.txt
```

## 2. Environment Variables (`.env`)
The `.env` file is used to securely store sensitive credentials outside of the source code. You must create a `.env` file in the project root before launching the stack.

**Structure :**

`MONGO_ROOT_USERNAME=your_secure_username`  
`MONGO_ROOT_PASSWORD=your_secure_password`

> **Note: Never push your actual `.env` file to version control. It should be added to your `.gitignore`).**

## 3. Docker Infrastructure (`docker-compose.yml`)

The `docker-compose.yml` file defines and configures **two services** on a shared Docker network (`p05_network`):

* **`mongodb`** : the database. It maps the local port `27017` to the container, reads the `.env` file to create the root user (`MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD`), and stores its data in the persistent volume `mongodb_data` so nothing is lost when the container stops.
* **`migration`** : built from the local `Dockerfile` (installs `requirements.txt` at build time). It mounts the `data/` folder (containing `healthcare_dataset.csv`) as a volume, waits for `mongodb` to be ready (`depends_on`), and runs `migrate.py` on startup.

**Authentication :** the `migration` service connects to MongoDB using the same root credentials from `.env`, with `authSource=admin`. The container reaches the database using the Docker service name `mongodb` as the host (via the `MONGO_HOST` environment variable, injected by `docker-compose.yml`) instead of `localhost`, since both containers communicate over the internal `p05_network`.

**How to launch the whole stack (database + migration) :**  
Open your terminal in the project folder and run :
```bash
docker compose up --build
```
This single command builds the `migration` image, starts MongoDB, and executes the ETL script automatically.

**To (re-)run only the migration script**, for example after modifying the CSV :
```bash
docker compose run migration python migrate.py
```

To stop the stack, use : 
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
Le fichier `requirements.txt` liste toutes les bibliothèques Python externes nécessaires au bon fonctionnement de ce script (`pandas`, `pymongo`, `python-dotenv`, `pytest`). Avec Docker (recommandé, voir section 3), ces dépendances sont installées **automatiquement** lors du build de l'image : aucune installation manuelle n'est nécessaire.

**Installation manuelle (uniquement si vous voulez exécuter `migrate.py` hors Docker) :**
Il est recommandé de créer et d'activer d'abord un environnement virtuel. Ensuite, installez les dépendances en exécutant la commande suivante dans votre terminal :
```bash
pip install -r requirements.txt
```

## 2. Variables d'environnement (`.env`)
Le fichier `.env` permet de stocker vos identifiants sensibles de manière sécurisée, en dehors du code source. Vous devez créer un fichier `.env` à la racine du projet avant de lancer la stack.

**Structure :**

`MONGO_ROOT_USERNAME=your_secure_username`  
`MONGO_ROOT_PASSWORD=your_secure_password`

> **Note : Ne publiez jamais votre véritable fichier `.env` sur un gestionnaire de version comme Git. Il doit être ignoré via le fichier `.gitignore`.**

## 3. Infrastructure Docker (`docker-compose.yml`)

Le fichier `docker-compose.yml` définit et configure **deux services** reliés par un réseau Docker partagé (`p05_network`) :

* **`mongodb`** : la base de données. Il redirige le port `27017` vers votre machine, lit le fichier `.env` pour créer l'utilisateur administrateur (`MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD`), et stocke ses données dans le volume persistant `mongodb_data` pour qu'elles ne soient pas perdues à l'arrêt du conteneur.
* **`migration`** : construit à partir du `Dockerfile` local (installe `requirements.txt` au moment du build). Il monte le dossier `data/` (contenant `healthcare_dataset.csv`) en volume, attend que `mongodb` soit prêt (`depends_on`), puis exécute `migrate.py` au démarrage.

**Authentification :** le service `migration` se connecte à MongoDB avec les mêmes identifiants administrateur définis dans `.env`, via `authSource=admin`. Le conteneur joint la base de données en utilisant le nom du service Docker `mongodb` comme hôte (via la variable d'environnement `MONGO_HOST`, injectée par `docker-compose.yml`) plutôt que `localhost`, car les deux conteneurs communiquent via le réseau interne `p05_network`.

**Comment lancer toute la stack (base de données + migration) :**  
Ouvrez votre terminal dans le dossier du projet et exécutez :
```bash
docker compose up --build
```
Cette commande unique construit l'image `migration`, démarre MongoDB, puis exécute automatiquement le script ETL.

**Pour ré-exécuter uniquement le script de migration**, par exemple après avoir modifié le CSV :
```bash
docker compose run migration python migrate.py
```

Pour arrêter la stack, utilisez la commande
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