#!/usr/bin/env python3
"""
Complete Drishti AI Safety Agent
- Fetches videos from Cloud Storage bucket and analyzes them
- Performs live YOLO detection with threshold alerts
- Sends alerts to dashboard in real-time
"""

import asyncio
import cv2
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path

# AI and Cloud imports
from ultralytics import YOLO
import google.generativeai as genai
from google.cloud import storage, firestore
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore
import requests
from twilio.rest import Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteDrishtiAIAgent:
    def __init__(self):
        """Initialize the complete AI agent"""
        # Configuration - Set first!
        self.PEOPLE_THRESHOLD = 10  # Alert if more than 10 people (lowered for testing)
        self.RISK_THRESHOLD = 0.7   # Alert if risk > 70%
        self.CHECK_INTERVAL = 30    # Check every 30 seconds
        self.BUCKET_NAME = "drishti-video-input"  # User's actual bucket name
        self.VIDEO_FOLDER = ""  # Videos are in root folder
        
        # Initialize services
        self.setup_firebase()
        self.setup_ai_models()
        self.setup_cloud_storage()
        self.setup_notifications()
        
        # Stats tracking
        self.stats = {
            'detections': 0,
            'alerts_sent': 0,
            'videos_processed': 0,
            'start_time': datetime.now()
        }
        
        logger.info("🤖 Complete Drishti AI Agent initialized!")
    
    def setup_firebase(self):
        """Initialize Firebase"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("firebase-key.json")
                firebase_admin.initialize_app(cred)
            self.db = admin_firestore.client()
            logger.info("✅ Firebase initialized")
        except Exception as e:
            logger.error(f"❌ Firebase setup error: {e}")
    
    def setup_ai_models(self):
        """Initialize AI models"""
        try:
            # Initialize YOLO
            self.yolo_model = YOLO('yolov8n.pt')
            logger.info("✅ YOLOv8 model loaded")
            
            # Initialize Gemini
            genai.configure(api_key=os.getenv('GEMINI_API_KEY', 'XXXXXXXXXXXXXX'))
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
            logger.info("✅ Gemini AI initialized")
            
        except Exception as e:
            logger.error(f"❌ AI models setup error: {e}")
    
    def setup_cloud_storage(self):
        """Initialize Google Cloud Storage"""
        try:
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(self.BUCKET_NAME)
            logger.info("✅ Cloud Storage initialized")
        except Exception as e:
            logger.error(f"❌ Cloud Storage setup error: {e}")
    
    def setup_notifications(self):
        """Initialize Twilio for notifications"""
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your-account-sid')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your-auth-token')
            self.twilio_client = Client(account_sid, auth_token)
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
            self.receiver_phone = os.getenv('RECEIVER_PHONE_NUMBER', '+1234567890')
            logger.info("✅ Twilio notifications initialized")
        except Exception as e:
            logger.error(f"❌ Twilio setup error: {e}")
    
    async def fetch_videos_from_bucket(self) -> List[str]:
        """Fetch video files from Cloud Storage bucket"""
        try:
            video_uris = []
            blobs = self.bucket.list_blobs(prefix=self.VIDEO_FOLDER)
            
            for blob in blobs:
                if blob.name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    video_uri = f"gs://{self.BUCKET_NAME}/{blob.name}"
                    video_uris.append(video_uri)
                    logger.info(f"📹 Found video: {blob.name}")
            
            return video_uris
        except Exception as e:
            logger.error(f"❌ Error fetching videos: {e}")
            return []
    
    def analyze_video_with_yolo(self, video_path: str) -> Dict:
        """Analyze video using YOLO for people detection"""
        try:
            if video_path.startswith('gs://'):
                # Download from cloud storage for local processing
                blob_name = video_path.replace(f"gs://{self.BUCKET_NAME}/", "")
                blob = self.bucket.blob(blob_name)
                local_path = f"temp_{blob_name.split('/')[-1]}"
                blob.download_to_filename(local_path)
                video_path = local_path
            
            cap = cv2.VideoCapture(video_path)
            total_people = 0
            frame_count = 0
            max_people_in_frame = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 30th frame for efficiency
                if frame_count % 30 == 0:
                    results = self.yolo_model(frame)
                    people_in_frame = 0
                    
                    for result in results:
                        boxes = result.boxes
                        if boxes is not None:
                            for box in boxes:
                                if int(box.cls[0]) == 0:  # Person class
                                    people_in_frame += 1
                    
                    total_people += people_in_frame
                    max_people_in_frame = max(max_people_in_frame, people_in_frame)
                
                frame_count += 1
            
            cap.release()
            
            # Clean up temporary file
            if video_path.startswith('temp_'):
                os.remove(video_path)
            
            avg_people = total_people / max(1, frame_count // 30)
            
            analysis = {
                'total_people': total_people,
                'max_people_in_frame': max_people_in_frame,
                'avg_people_per_frame': avg_people,
                'frame_count': frame_count,
                'video_path': video_path
            }
            
            logger.info(f"📊 Video analysis: Max {max_people_in_frame} people, Avg {avg_people:.1f}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Video analysis error: {e}")
            return {'max_people_in_frame': 0, 'error': str(e)}
    
    async def analyze_with_gemini(self, people_count: int, location: str) -> Dict:
        """Analyze crowd situation with Gemini AI"""
        try:
            prompt = f"""
            Analyze this crowd situation:
            - Location: {location}
            - People count: {people_count}
            - Context: Public safety monitoring
            
            Provide a risk assessment (0.0-1.0) and brief description.
            Return only: RISK_SCORE|DESCRIPTION
            Example: 0.8|High crowd density detected, potential safety concern
            """
            
            response = self.gemini_model.generate_content(prompt)
            result = response.text.strip()
            
            if '|' in result:
                risk_str, description = result.split('|', 1)
                risk_score = float(risk_str)
            else:
                risk_score = 0.5
                description = "Standard crowd monitoring"
            
            return {
                'risk_score': risk_score,
                'description': description,
                'people_count': people_count
            }
            
        except Exception as e:
            logger.error(f"❌ Gemini analysis error: {e}")
            return {
                'risk_score': 0.5,
                'description': f"Analysis unavailable - {people_count} people detected",
                'confidence': 0.3
            }
    
    async def log_detection_data(self, people_count: int, risk_score: float = None, source: str = "Live Camera"):
        """Log detection data to Firestore for dashboard display"""
        try:
            detection_data = {
                'people_count': people_count,
                'risk_score': risk_score or 0.0,
                'source': source,
                'timestamp': admin_firestore.SERVER_TIMESTAMP,
                'location': 'Live Camera Feed',
                'confidence': 0.95
            }
            
            # Store in detections collection for dashboard
            self.db.collection('detections').add(detection_data)
            logger.info(f"📊 Detection data logged: {people_count} people, risk: {risk_score:.2f}" if risk_score else f"📊 Detection data logged: {people_count} people")
            
        except Exception as e:
            logger.error(f"❌ Error logging detection data: {e}")
    
    async def create_alert(self, analysis: Dict, source: str, location: str) -> str:
        """Create and store alert in Firestore"""
        try:
            people_count = analysis.get('max_people_in_frame', analysis.get('people_count', 0))
            
            # Get risk assessment from Gemini
            gemini_analysis = await self.analyze_with_gemini(people_count, location)
            risk_score = gemini_analysis['risk_score']
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = 'High'
            elif risk_score >= 0.5:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
        except Exception as e:
            logger.error(f"❌ Alert creation error: {e}")
            return None
    
    async def send_emergency_notification(self, alert_data: Dict):
        """Send emergency SMS notification"""
        try:
            message = f"""
🚨 DRISHTI EMERGENCY ALERT 🚨
Location: {alert_data['location']}
People: {alert_data['people_count']}
Risk: {alert_data['risk_level']}
Time: {datetime.now().strftime('%H:%M:%S')}
Description: {alert_data['description']}
            """.strip()
            
            self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=self.receiver_phone
            )
            
            logger.info("📱 Emergency SMS sent!")
            
        except Exception as e:
            logger.error(f"❌ SMS notification error: {e}")
    
    async def live_camera_monitoring(self):
        """Monitor live camera feed with YOLO"""
        logger.info("📹 Starting live camera monitoring...")
        
        try:
            cap = cv2.VideoCapture(0)  # Use default camera
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("⚠️ No camera feed available, using test data")
                    break
                
                # Run YOLO detection
                results = self.yolo_model(frame)
                people_count = 0
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            if int(box.cls[0]) == 0:  # Person class
                                people_count += 1
                
                self.stats['detections'] += 1
                
                # Log detection data for dashboard (every detection)
                risk_score = 0.3 if people_count < 5 else 0.6 if people_count < 10 else 0.9
                await self.log_detection_data(
                    people_count=people_count,
                    risk_score=risk_score,
                    source="Live Camera"
                )
                
                # Check threshold for alerts
                if people_count >= self.PEOPLE_THRESHOLD:
                    analysis = {
                        'people_count': people_count,
                        'max_people_in_frame': people_count,
                        'confidence': 0.9
                    }
                    
                    await self.create_alert(
                        analysis=analysis,
                        source="Live Camera",
                        location="Live Monitoring Zone"
                    )
                
                logger.info(f"👥 Live detection: {people_count} people")
                
                # Wait before next check
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"❌ Live monitoring error: {e}")
        finally:
            if 'cap' in locals():
                cap.release()
    
    async def bucket_video_monitoring(self):
        """Monitor and analyze videos from Cloud Storage bucket"""
        logger.info("☁️ Starting bucket video monitoring...")
        
        while True:
            try:
                # Fetch videos from bucket
                video_uris = await self.fetch_videos_from_bucket()
                
                for video_uri in video_uris:
                    logger.info(f"🎥 Processing video: {video_uri}")
                    
                    # Analyze video
                    analysis = self.analyze_video_with_yolo(video_uri)
                    people_count = analysis.get('max_people_in_frame', 0)
                    
                    # Check if alert needed
                    if people_count >= self.PEOPLE_THRESHOLD:
                        location = self.extract_location_from_uri(video_uri)
                        await self.create_alert(
                            analysis=analysis,
                            source="Cloud Storage Video",
                            location=location
                        )
                    
                    self.stats['videos_processed'] += 1
                    
                    # Small delay between videos
                    await asyncio.sleep(2)
                
                # Wait before next bucket check
                await asyncio.sleep(self.CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"❌ Bucket monitoring error: {e}")
                await asyncio.sleep(10)
    
    def extract_location_from_uri(self, video_uri: str) -> str:
        """Extract location from video URI"""
        if 'main-gate' in video_uri.lower():
            return 'Main Gate - Sector A'
        elif 'food-court' in video_uri.lower():
            return 'Food Court Area'
        elif 'parking' in video_uri.lower():
            return 'Parking Lot B'
        elif 'crowd' in video_uri.lower():
            return 'Crowd Monitoring Zone'
        else:
            return 'Unknown Location'
    
    async def system_monitor(self):
        """Monitor system health and stats"""
        while True:
            uptime = datetime.now() - self.stats['start_time']
            logger.info(f"📊 System Stats - Uptime: {uptime}, Detections: {self.stats['detections']}, Alerts: {self.stats['alerts_sent']}, Videos: {self.stats['videos_processed']}")
            await asyncio.sleep(60)  # Log every minute
    
    async def run_complete_system(self):
        """Run the complete AI agent system"""
        logger.info("🚀 Starting Complete Drishti AI Safety System!")
        
        # Create tasks for parallel execution
        tasks = [
            asyncio.create_task(self.live_camera_monitoring()),
            asyncio.create_task(self.bucket_video_monitoring()),
            asyncio.create_task(self.system_monitor())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("🛑 System shutdown requested")
        except Exception as e:
            logger.error(f"❌ System error: {e}")

async def main():
    """Main function"""
    agent = CompleteDrishtiAIAgent()
    await agent.run_complete_system()

if __name__ == "__main__":
    asyncio.run(main())
