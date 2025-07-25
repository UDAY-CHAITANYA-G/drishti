// fcm-init.js

console.log('fcm-init.js loaded');

// Initialize Firebase app (config is loaded from config.js)
const app = firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

// Register service worker for FCM
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/firebase-messaging-sw.js')
    .then(function(registration) {
      // Request notification permission from the user
      return Notification.requestPermission().then(function(permission) {
        if (permission === 'granted') {
          // Get the FCM token with VAPID key
          return messaging.getToken({
            vapidKey: 'BMqC1Fskv48Y5425zmsc06FozCXIBA27R76tucywtpNPNjWC6_v22d_HSwgl0JVC9kODAkyAr6o_Mma1WY6QxhY', // <-- Replace with your actual VAPID key
            serviceWorkerRegistration: registration
          });
        } else {
          throw new Error('Notification permission not granted');
        }
      });
    })
    .then(function(token) {
      if (token) {
        console.log('FCM token:', token);
      } else {
        console.log('No registration token available. Request permission to generate one.');
      }
    })
    .catch(function(err) {
      console.error('FCM error:', err);
    });
} 