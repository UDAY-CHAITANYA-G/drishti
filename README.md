# Drishti Cloud Functions

This project contains Firebase Cloud Functions for the Drishti application.

## Features

- **helloWorld Function:**
  Responds with a simple greeting message.

- **testFirestore Function:**
  Writes a test document to Firestore and returns its data.

## Prerequisites

- [Node.js](https://nodejs.org/) (v22.x recommended)
- [Firebase CLI](https://firebase.google.com/docs/cli) (`npm install -g firebase-tools`)
- A Firebase project (set up via `firebase init`)

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd drishti
   ```

2. **Install dependencies:**
   ```sh
   cd functions
   npm install
   ```

3. **Set up Firebase:**
   - Log in:  
     ```sh
     firebase login
     ```
   - Set your project:  
     ```sh
     firebase use --add
     ```

## Local Development

### Run Functions Emulator

```sh
firebase emulators:start --only functions
```

### Test Functions

- **helloWorld:**  
  Visit: `http://localhost:5001/<your-project-id>/us-central1/helloWorld`

- **testFirestore:**  
  Visit: `http://localhost:5001/<your-project-id>/us-central1/testFirestore`

## Deployment

Deploy your functions to Firebase:

```sh
firebase deploy --only functions
```

## Linting

Run ESLint to check for code issues:

```sh
cd functions
npm run lint
```

## Project Structure

```
drishti/
  ├── functions/
  │   ├── index.js         # Cloud Functions source code
  │   ├── package.json     # Functions dependencies and scripts
  │   └── .eslintrc.js     # ESLint configuration
  ├── public/              # (If using Firebase Hosting)
  └── firebase.json        # Firebase project configuration
```

## Notes

- Ensure your Firestore database is set up in the Firebase Console for the `testFirestore` function to work.
- Update security rules as needed in `firestore.rules`. 