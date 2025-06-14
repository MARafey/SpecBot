# firebase_config.py
import firebase_admin
from firebase_admin import credentials

# Path to your Firebase service account JSON file
cred = credentials.Certificate('Jsons/file.json')
firebase_admin.initialize_app(cred)
