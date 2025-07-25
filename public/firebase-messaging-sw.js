importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Initialize Firebase in the service worker (replace with your config)
const firebaseConfig = {
    apiKey: "AIzaSyDbBtRoKrqwSd1lnc2PmRX2Onv96mOjZoY",
    authDomain: "drishti-public-safety.firebaseapp.com",
    databaseURL: "https://drishti-public-safety-default-rtdb.firebaseio.com",
    projectId: "drishti-public-safety",
    storageBucket: "drishti-public-safety.firebasestorage.app",
    messagingSenderId: "467353691794",
    appId: "1:467353691794:web:39ac14faed31991e30684b",
    measurementId: "G-DMKQGYVB54"
  };

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage(payload => {
  console.log('Received background message:', payload);
  const title = payload.notification.title;
  const options = { body: payload.notification.body };
  self.registration.showNotification(title, options);
});

// Optional: Respond to message events to avoid message port warnings
self.addEventListener('message', (event) => {
  console.log('Message received in service worker:', event);
  event.ports[0]?.postMessage({ status: 'ok' });
}); 