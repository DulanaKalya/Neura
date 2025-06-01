# Firebase Setup Guide for SafeBridge

This guide will help you set up Firebase for your SafeBridge application.

## Creating a Firebase Project

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click on "Add project"
3. Enter "SafeBridge" as your project name
4. Choose whether to enable Google Analytics (optional)
5. Click "Create project"

## Setting Up Firestore Database

1. In your Firebase project dashboard, click on "Build" in the left sidebar
2. Select "Firestore Database"
3. Click "Create database"
4. Choose "Start in production mode" (recommended for better security)
5. Select a location for your database that's closest to your users
6. Click "Enable"

### Setting Up Database Security Rules

1. In Firestore Database, click on the "Rules" tab
2. Replace the default rules with the following:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection
    match /users/{userId} {
      // Anyone can create a user document
      allow create;
      // Only authenticated users can read their own user document
      allow read: if request.auth != null && (request.auth.uid == userId || get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'first_responder');
      // Only the user themselves can update their document
      allow update: if request.auth != null && request.auth.uid == userId;
    }
    
    // Requests collection
    match /requests/{requestId} {
      // Anyone can create a request
      allow create: if request.auth != null;
      // Anyone can read requests
      allow read;
      // Only first responders and volunteers can update requests
      allow update: if request.auth != null && 
        (get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'first_responder' || 
         get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'volunteer');
    }
    
    // Volunteers collection
    match /volunteers/{volunteerId} {
      // Anyone can create a volunteer profile
      allow create: if request.auth != null;
      // Anyone can read volunteer profiles
      allow read;
      // Only the volunteer themselves or first responders can update
      allow update: if request.auth != null && 
        (request.auth.uid == volunteerId || 
         get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'first_responder');
    }
  }
}
```

3. Click "Publish"

## Generating Admin SDK Credentials

For your Python backend to interact with Firebase, you'll need Admin SDK credentials:

1. In your Firebase project, click on the gear icon (⚙️) next to "Project Overview" and select "Project settings"
2. Go to the "Service accounts" tab
3. Click "Generate new private key"
4. Save the JSON file securely (this file contains sensitive credentials)
5. Place this file in your project's backend directory or reference it through environment variables

## Setting Up Environment Variables

Create a `.env` file in your project's root directory with:

```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/firebase-credentials.json
```

If you're deploying to a hosting service, set this environment variable in your deployment configuration.

## Initializing Firebase Admin SDK

In your Python code, initialize Firebase Admin SDK:

```python
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase
cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()
```

## Database Collections Structure

Create the following collections in Firestore:

### Users Collection

Each document represents a user with fields:
- id: string
- email: string
- password: string (in production, use Firebase Auth instead)
- fullName: string
- role: string ('affected_individual', 'volunteer', or 'first_responder')
- location: string
- created_at: timestamp

### Requests Collection

Each document represents an emergency request:
- id: string
- text: string
- urgency: string ('High', 'Medium', 'Low', or 'Unknown')
- type: string ('Medical', 'Food', 'Shelter', 'Evacuation', or 'Other')
- location: string
- timestamp: timestamp
- status: string ('pending', 'processing', or 'resolved')
- lastUpdated: timestamp (optional)

### Volunteers Collection

Each document represents a volunteer or first responder profile:
- id: string
- email: string
- name: string
- role: string ('volunteer' or 'first_responder')
- location: string
- specialties: array of strings
- availability: string
- experience: string
- created_at: timestamp

## Security Recommendations

1. In production, use Firebase Authentication instead of storing passwords in Firestore
2. Set up proper Firestore security rules to protect your data
3. Keep your service account key secure and never commit it to version control
4. Consider implementing role-based access control on both frontend and backend

## Next Steps

Once Firebase is set up:

1. Initialize your Streamlit application
2. Connect it to Firebase using the Admin SDK
3. Test user registration and authentication
4. Implement request submission and management features
