import os

from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env
load_dotenv()

# Aucune valeur sensible en dur : tout est lu depuis l'environnement
DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5433"),
}