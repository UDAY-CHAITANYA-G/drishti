#!/usr/bin/env python3
"""
🚨 DRISHTI MASTER AI AGENT 🚨
Complete unified orchestrator integrating ALL existing components:
- Real-time camera feeds with YOLOv8
- Vertex AI video analysis
- Gemini risk assessment
- Firebase logging and alerts
- Twilio emergency notifications
- Live dashboard updates
"""

import os
import sys
import time
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional
import json

# Add all component paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'realtime'))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'event-ai-system'))

# Import all existing components
import cv2
from ultralytics import YOLO
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
from twilio.rest import Client
from google.cloud import storage

# Import existing modules
from vertex_vision_detect import run_object_detection
from realtime.risk_analysis import analyze_risk
from realtime.firebase_logger import log_event
from realtime.alert_system import send_alert as send_twilio_alert
from realtime.config import VIDEO_SOURCE, RISK_THRESHOLD, GEMINI_API_KEY

class DrishtiMasterAgent:
    """🤖 Master AI Agent orchestrating all Drishti safety systems"""
    
    def __init__(self):
        """Initialize all subsystems"""
        print("🚀 Initializing Drishti Master AI Agent...")
        
        # Core configuration
        self.project_id = "drishti-public-safety"
        self.region = "us-central1"
        
        # Initialize Firebase
        self._init_firebase()
        
        # Initialize AI models
        self._init_ai_models()
        
        # Initialize communication systems
        self._init_communications()
        
        # System state
        self.active_feeds = {}
        self.alert_history = []
        self.system_stats = {
            'total_detections': 0,
            'alerts_sent': 0,
            'high_risk_events': 0,
            'system_uptime': datetime.now()
        }
        
        print("✅ Drishti Master Agent initialized successfully!")
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Try to get existing app
            self.firebase_app = firebase_admin.get_app()
        except ValueError:
            # Initialize new app
            key_path = os.path.join(os.path.dirname(__file__), 'firebase-key.json')
            if os.path.exists(key_path):
                cred = credentials.Certificate(key_path)
            else:
                cred = credentials.ApplicationDefault()
            
            self.firebase_app = firebase_admin.initialize_app(cred, {
                'projectId': self.project_id
            })
        
        self.db = firestore.client()
        self.storage_client = storage.Client()
        print("✅ Firebase initialized")
    
    def _init_ai_models(self):
        """Initialize AI models"""
        # YOLOv8 for real-time detection
        model_path = os.path.join(os.path.dirname(__file__), 'yolov8n.pt')
        self.yolo_model = YOLO(model_path if os.path.exists(model_path) else "yolov8n.pt")
        
        # Gemini for risk analysis
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        print("✅ AI models loaded")
    
    def _init_communications(self):
        """Initialize communication systems"""
        # Twilio for emergency alerts
        self.twilio_client = None
        try:
            if all([os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")]):
                self.twilio_client = Client(
                    os.getenv("TWILIO_ACCOUNT_SID"),
                    os.getenv("TWILIO_AUTH_TOKEN")
                )
                print("✅ Twilio initialized")
        except Exception as e:
            print(f"⚠️ Twilio not available: {e}")
    
    async def process_realtime_feed(self, source_id: str = "default"):
        """🎥 Process real-time camera feed with full AI pipeline"""
        print(f"📹 Starting real-time processing for source: {source_id}")
        
        cap = cv2.VideoCapture(VIDEO_SOURCE)
        if not cap.isOpened():
            print(f"❌ Cannot open video source: {VIDEO_SOURCE}")
            return
        
        last_gemini_call = 0
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Run YOLOv8 detection every frame
                results = self.yolo_model(frame)[0]
                
                # Filter for people (class 0)
                person_boxes = [
                    results.boxes.xyxy[i].tolist() 
                    for i, cls in enumerate(results.boxes.cls) 
                    if int(cls) == 0
                ]
                people_count = len(person_boxes)
                
                # Enhanced risk analysis every 3 seconds
                current_time = time.time()
                risk_score = 0.0
                
                if people_count > 0 and (current_time - last_gemini_call) >= 3:
                    # Multi-layer risk analysis
                    risk_score = await self._comprehensive_risk_analysis(
                        people_count, person_boxes, frame, source_id
                    )
                    last_gemini_call = current_time
                
                # Generate alerts based on risk
                await self._process_risk_alert(risk_score, people_count, source_id)
                
                # Update live dashboard
                await self._update_dashboard(people_count, risk_score, source_id)
                
                # Visualize (optional)
                if os.getenv("SHOW_DISPLAY", "false").lower() == "true":
                    self._draw_detections(frame, person_boxes, people_count, risk_score)
                    cv2.imshow(f"Drishti Live - {source_id}", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Brief pause to prevent overwhelming
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("🛑 Real-time processing stopped")
        finally:
            cap.release()
            cv2.destroyAllWindows()
    
    async def _comprehensive_risk_analysis(self, people_count: int, positions: List, frame, source_id: str) -> float:
        """🧠 Multi-layer AI risk analysis"""
        try:
            # Layer 1: Gemini crowd analysis
            gemini_risk = analyze_risk(people_count, positions)
            
            # Layer 2: Density analysis
            frame_area = frame.shape[0] * frame.shape[1]
            density_risk = min(people_count / (frame_area / 100000), 1.0)  # Normalize
            
            # Layer 3: Movement pattern analysis (simplified)
            movement_risk = 0.5  # Placeholder for movement analysis
            
            # Weighted combination
            combined_risk = (
                gemini_risk * 0.5 +
                density_risk * 0.3 +
                movement_risk * 0.2
            )
            
            print(f"🎯 Risk Analysis - Gemini: {gemini_risk:.2f}, Density: {density_risk:.2f}, Combined: {combined_risk:.2f}")
            return min(combined_risk, 1.0)
            
        except Exception as e:
            print(f"⚠️ Risk analysis error: {e}")
            return 0.5
    
    async def _process_risk_alert(self, risk_score: float, people_count: int, source_id: str):
        """🚨 Process and send alerts based on risk level"""
        if risk_score >= RISK_THRESHOLD:
            alert_data = {
                'title': f"High Risk Crowd Alert - {source_id}",
                'location': self._get_location_name(source_id),
                'people_count': people_count,
                'risk_level': self._get_risk_level(risk_score),
                'risk_score': risk_score,
                'status': 'Active',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'source_id': source_id,
                'alert_type': 'realtime_detection',
                'agent_generated': True
            }
            
            # Store in Firestore
            doc_ref = self.db.collection('alerts').add(alert_data)
            alert_id = doc_ref[1].id
            
            # Send Twilio alert for high risk
            if risk_score >= 0.8 and self.twilio_client:
                await self._send_emergency_notification(alert_data)
            
            # Update stats
            self.system_stats['alerts_sent'] += 1
            if risk_score >= 0.8:
                self.system_stats['high_risk_events'] += 1
            
            print(f"🚨 Alert generated: {alert_id} - Risk: {risk_score:.2f}")
    
    async def _send_emergency_notification(self, alert_data: Dict):
        """📱 Send emergency notifications via Twilio"""
        try:
            message_body = (
                f"🚨 DRISHTI EMERGENCY ALERT 🚨\n"
                f"Location: {alert_data['location']}\n"
                f"People Count: {alert_data['people_count']}\n"
                f"Risk Level: {alert_data['risk_level']}\n"
                f"Risk Score: {alert_data['risk_score']:.2f}\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=os.getenv("RECEIVER_PHONE_NUMBER")
            )
            
            print(f"📱 Emergency notification sent: {message.sid}")
            
        except Exception as e:
            print(f"❌ Failed to send emergency notification: {e}")
    
    async def _update_dashboard(self, people_count: int, risk_score: float, source_id: str):
        """📊 Update live dashboard with current data"""
        try:
            # Log real-time event to Firestore
            log_event(
                person_count=people_count,
                risk_score=risk_score,
                alert_triggered=risk_score >= RISK_THRESHOLD,
                source_id=source_id
            )
            
            # Update system stats
            self.system_stats['total_detections'] += 1
            
        except Exception as e:
            print(f"⚠️ Dashboard update error: {e}")
    
    async def process_vertex_ai_batch(self, video_uris: List[str]):
        """☁️ Process video batches using Vertex AI"""
        print("☁️ Processing Vertex AI batch analysis...")
        
        for video_uri in video_uris:
            try:
                # Use existing Vertex AI function
                result = await asyncio.to_thread(run_object_detection, video_uri)
                
                if result and 'person_count' in result:
                    people_count = result['person_count']
                    risk_score = self._calculate_vertex_risk(people_count)
                    
                    # Generate alert if needed
                    if risk_score >= RISK_THRESHOLD:
                        alert_data = {
                            'title': f"Vertex AI Crowd Alert",
                            'location': self._extract_location_from_uri(video_uri),
                            'people_count': people_count,
                            'risk_level': self._get_risk_level(risk_score),
                            'status': 'Active',
                            'timestamp': firestore.SERVER_TIMESTAMP,
                            'video_source': video_uri,
                            'alert_type': 'vertex_ai_batch',
                            'agent_generated': True
                        }
                        
                        # Store alert
                        doc_ref = self.db.collection('alerts').add(alert_data)
                        print(f"☁️ Vertex AI alert generated: {doc_ref[1].id}")
                
            except Exception as e:
                print(f"❌ Vertex AI processing error: {e}")
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level string from score"""
        if risk_score >= 0.8:
            return 'High'
        elif risk_score >= 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _get_location_name(self, source_id: str) -> str:
        """Get human-readable location name"""
        location_map = {
            'default': 'Main Monitoring Area',
            'gate': 'Main Gate - Sector A',
            'food_court': 'Food Court Area',
            'parking': 'Parking Lot B'
        }
        return location_map.get(source_id, f'Location {source_id}')
    
    def _extract_location_from_uri(self, video_uri: str) -> str:
        """Extract location from video URI"""
        if 'main-gate' in video_uri.lower():
            return 'Main Gate - Sector A'
        elif 'food-court' in video_uri.lower():
            return 'Food Court Area'
        elif 'parking' in video_uri.lower():
            return 'Parking Lot B'
        else:
            return 'Unknown Location'
    
    def _calculate_vertex_risk(self, people_count: int) -> float:
        """Calculate risk from Vertex AI people count"""
        # Simple risk calculation - can be enhanced
        if people_count >= 50:
            return 0.9
        elif people_count >= 30:
            return 0.7
        elif people_count >= 15:
            return 0.5
        else:
            return 0.2
    
    def _draw_detections(self, frame, person_boxes: List, people_count: int, risk_score: float):
        """Draw detection visualizations on frame"""
        # Draw bounding boxes
        for box in person_boxes:
            x1, y1, x2, y2 = map(int, box)
            color = (0, 255, 0) if risk_score < 0.5 else (0, 165, 255) if risk_score < 0.8 else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Draw info overlay
        info_text = f"People: {people_count} | Risk: {risk_score:.2f}"
        cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Risk indicator
        risk_color = (0, 255, 0) if risk_score < 0.5 else (0, 165, 255) if risk_score < 0.8 else (0, 0, 255)
        cv2.circle(frame, (frame.shape[1] - 50, 50), 20, risk_color, -1)
    
    async def run_master_system(self):
        """🚀 Run the complete master system"""
        print("🚀 Starting Drishti Master AI System...")
        
        # Start multiple concurrent tasks
        tasks = []
        
        # Real-time monitoring
        tasks.append(asyncio.create_task(self.process_realtime_feed("main_camera")))
        
        # Vertex AI batch processing (if video sources available)
        vertex_videos = [
            'gs://drishti-public-safety.appspot.com/test-videos/crowd-sample.mp4'
        ]
        tasks.append(asyncio.create_task(self.process_vertex_ai_batch(vertex_videos)))
        
        # System monitoring
        tasks.append(asyncio.create_task(self._system_monitor()))
        
        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("🛑 Master system shutdown initiated")
        except Exception as e:
            print(f"❌ Master system error: {e}")
    
    async def _system_monitor(self):
        """📊 Monitor system health and stats"""
        while True:
            try:
                uptime = datetime.now() - self.system_stats['system_uptime']
                print(f"📊 System Stats - Uptime: {uptime}, Detections: {self.system_stats['total_detections']}, Alerts: {self.system_stats['alerts_sent']}")
                
                # Update system status in Firestore
                system_status = {
                    'status': 'online',
                    'uptime_seconds': uptime.total_seconds(),
                    'total_detections': self.system_stats['total_detections'],
                    'alerts_sent': self.system_stats['alerts_sent'],
                    'high_risk_events': self.system_stats['high_risk_events'],
                    'last_heartbeat': firestore.SERVER_TIMESTAMP
                }
                
                self.db.collection('system_status').document('master_agent').set(system_status)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                print(f"⚠️ System monitor error: {e}")
                await asyncio.sleep(10)

async def main():
    """🚀 Main entry point"""
    print("🚨 DRISHTI MASTER AI AGENT STARTING 🚨")
    
    # Initialize master agent
    master_agent = DrishtiMasterAgent()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            print("🧪 Running system test...")
            # Add test functionality here
        elif sys.argv[1] == 'realtime':
            await master_agent.process_realtime_feed()
        elif sys.argv[1] == 'vertex':
            await master_agent.process_vertex_ai_batch([
                'gs://drishti-public-safety.appspot.com/test-videos/crowd-sample.mp4'
            ])
    else:
        # Run complete master system
        await master_agent.run_master_system()

if __name__ == "__main__":
    asyncio.run(main())
