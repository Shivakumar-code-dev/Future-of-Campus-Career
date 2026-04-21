import firebase_admin
from firebase_admin import credentials, firestore, storage

# ─────────────────────────────────────────────────────────
# SETUP INSTRUCTIONS:
# 1. Go to Firebase Console → Project Settings → Service Accounts
# 2. Click "Generate new private key" → download serviceAccountKey.json
# 3. Place serviceAccountKey.json in this folder
# 4. Replace "your-project-id" below with your actual Firebase project ID
# ─────────────────────────────────────────────────────────

cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred, {
    "storageBucket": "your-project-id.appspot.com"
})

db = firestore.client()
bucket = storage.bucket()
