# SafeBridge: AI-Powered Disaster Response Platform (Streamlit Version)

This repository contains a streamlined version of SafeBridge using Streamlit and Google Firestore, making it easier to develop, deploy, and maintain.

## Project Overview

SafeBridge is an AI-powered platform that connects individuals affected by disasters with emergency services, volunteers, and resources in real-time. The platform enables:

- **Rapid Emergency Response** coordination
- **AI-Powered Resource Allocation**
- **Community-Driven Support Networks**

## Tech Stack

- **Frontend:** Streamlit (Python)
- **Backend:** Python
- **Database:** Google Firestore
- **Authentication:** Custom session management

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Google Firebase account
- Firebase project with Firestore database

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/safebridge-streamlit.git
cd safebridge-streamlit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Firebase:
   - Create a Firebase project at [firebase.google.com](https://firebase.google.com)
   - Enable Firestore database
   - Download your Firebase Admin SDK service account key (JSON file)
   - Rename it to `firebase-credentials.json` and place it in the project root or set the path as an environment variable

4. Create a `.env` file in the project root with the following:
```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/firebase-credentials.json
```

### Running the Application

Start the Streamlit application:

```bash
cd streamlit_app
streamlit run frontend/app.py
```

## Project Structure

```
streamlit_app/
├── frontend/
│   ├── app.py             # Main Streamlit app entry point
│   ├── pages/             # Multi-page Streamlit app structure
│   │   ├── 01_home.py
│   │   ├── 02_register.py
│   │   ├── 03_login.py
│   │   ├── 04_dashboard.py
│   │   ├── 05_request.py
│   │   └── 06_chat.py
│   ├── components/        # Reusable UI components
│   └── assets/            # Static assets (images, CSS)
├── backend/
│   ├── firebase_admin.py  # Firebase Admin SDK setup
│   ├── auth.py            # Authentication functions
│   ├── database.py        # Firestore database functions
│   └── utils/             # Helper functions
└── requirements.txt       # Project dependencies
```

## Features

- **User Authentication:** Register and login functionality with role-based access
- **Emergency Request Submission:** Submit requests with different urgency levels
- **Role-Based Dashboards:** Different views for affected individuals, volunteers, and first responders
- **Real-time Updates:** Track request status and priority assignments
- **AI Assistance:** AI-powered request prioritization and resource allocation

## User Roles

1. **Affected Individual:** People in need of assistance during emergencies
2. **Volunteer:** Community members offering help and resources
3. **First Responder:** Emergency service professionals coordinating response efforts

## Firebase Setup

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Firestore Database
4. Set up Authentication (Email/Password provider)
5. Go to Project Settings > Service Accounts > Generate new private key
6. Save the JSON file and set the path in your environment variables

## Development

To add new features or modify existing ones:

1. Frontend changes: Modify the Streamlit pages in `/frontend/pages/`
2. Backend changes: Update the database and authentication functions in `/backend/`
3. Run the application locally to test changes

## Deployment

For deployment, you can use:

- [Streamlit Sharing](https://streamlit.io/sharing)
- [Heroku](https://heroku.com)
- [Google App Engine](https://cloud.google.com/appengine)

Make sure to set the appropriate environment variables in your deployment environment.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature-name`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature-name`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.
