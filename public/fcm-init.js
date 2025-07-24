// Initialize Firebase app (config is loaded from config.js)
const app = firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Register service worker for FCM
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then(function(registration) {
      messaging.useServiceWorker(registration);
      // Request permission and get token
      return messaging.requestPermission()
        .then(() => messaging.getToken())
        .then(token => {
          console.log('FCM token:', token);
        })
        .catch(err => {
          console.error('FCM error:', err);
        });
    });
} 