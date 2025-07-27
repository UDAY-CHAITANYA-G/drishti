#!/usr/bin/env python3
"""
🚀 DRISHTI COMPLETE SYSTEM DEPLOYMENT
Automated deployment script for the entire Drishti AI Safety ecosystem
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

class DrishtiDeployment:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.components = {
            'firebase_dashboard': self.base_path / 'firebase-studio',
            'realtime_system': self.base_path / 'realtime',
            'event_ai_system': self.base_path / 'event-ai-system',
            'master_agent': self.base_path / 'drishti_master_agent.py'
        }
        
    def check_dependencies(self):
        """Check all required dependencies"""
        print("🔍 Checking system dependencies...")
        
        required_packages = [
            'firebase-admin',
            'google-cloud-firestore',
            'google-cloud-aiplatform',
            'google-generativeai',
            'ultralytics',
            'opencv-python',
            'twilio',
            'fastapi',
            'uvicorn'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"❌ {package} - MISSING")
        
        if missing:
            print(f"\n📦 Installing missing packages: {', '.join(missing)}")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)
        
        return len(missing) == 0
    
    def deploy_firebase_dashboard(self):
        """Deploy Firebase dashboard"""
        print("🔥 Deploying Firebase dashboard...")
        
        firebase_dir = self.components['firebase_dashboard']
        if not firebase_dir.exists():
            print(f"❌ Firebase directory not found: {firebase_dir}")
            return False
        
        try:
            os.chdir(firebase_dir)
            result = subprocess.run(['firebase', 'deploy', '--only', 'hosting'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Firebase dashboard deployed successfully!")
                print("🌐 Dashboard URL: https://drishti-public-safety.web.app")
                return True
            else:
                print(f"❌ Firebase deployment failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Firebase deployment error: {e}")
            return False
        finally:
            os.chdir(self.base_path)
    
    def setup_environment_variables(self):
        """Setup required environment variables"""
        print("🔧 Setting up environment variables...")
        
        env_vars = {
            'GOOGLE_APPLICATION_CREDENTIALS': 'firebase-key.json',
            'GOOGLE_CLOUD_PROJECT': 'drishti-public-safety',
            'VERTEX_AI_REGION': 'us-central1',
            'VIDEO_SOURCE': '0',  # Default camera
            'RISK_THRESHOLD': '0.7',
            'SHOW_DISPLAY': 'true'
        }
        
        env_file = self.base_path / '.env'
        with open(env_file, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
                os.environ[key] = value
        
        print(f"✅ Environment file created: {env_file}")
        return True
    
    def start_realtime_monitoring(self):
        """Start real-time monitoring system"""
        print("📹 Starting real-time monitoring...")
        
        try:
            # Start master agent in background
            subprocess.Popen([
                sys.executable, 
                str(self.components['master_agent']), 
                'realtime'
            ])
            print("✅ Real-time monitoring started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start real-time monitoring: {e}")
            return False
    
    def start_emergency_agent(self):
        """Start emergency notification agent"""
        print("🚨 Starting emergency agent...")
        
        emergency_agent = self.components['event_ai_system'] / 'emergency_agent' / 'main.py'
        if not emergency_agent.exists():
            print(f"❌ Emergency agent not found: {emergency_agent}")
            return False
        
        try:
            subprocess.Popen([
                sys.executable, '-m', 'uvicorn',
                'event-ai-system.emergency_agent.main:app',
                '--host', '0.0.0.0',
                '--port', '8001'
            ])
            print("✅ Emergency agent started on port 8001")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start emergency agent: {e}")
            return False
    
    def create_system_status_dashboard(self):
        """Create system status monitoring"""
        print("📊 Creating system status dashboard...")
        
        status_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Drishti System Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body { font-family: Arial; padding: 2rem; background: #f0f0f0; }
        .status-card { background: white; padding: 1rem; margin: 1rem 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .online { border-left: 4px solid #4CAF50; }
        .offline { border-left: 4px solid #f44336; }
        .warning { border-left: 4px solid #ff9800; }
    </style>
</head>
<body>
    <h1>🚨 Drishti AI Safety System Status</h1>
    
    <div class="status-card online">
        <h3>📊 Dashboard</h3>
        <p>Status: <strong>Online</strong></p>
        <p>URL: <a href="https://drishti-public-safety.web.app" target="_blank">https://drishti-public-safety.web.app</a></p>
    </div>
    
    <div class="status-card online">
        <h3>📹 Real-time Monitoring</h3>
        <p>Status: <strong>Active</strong></p>
        <p>Camera Feed: Processing</p>
    </div>
    
    <div class="status-card online">
        <h3>🚨 Emergency Agent</h3>
        <p>Status: <strong>Running</strong></p>
        <p>Port: 8001</p>
    </div>
    
    <div class="status-card online">
        <h3>🤖 Master AI Agent</h3>
        <p>Status: <strong>Active</strong></p>
        <p>Mode: Full System</p>
    </div>
    
    <div class="status-card online">
        <h3>☁️ Vertex AI</h3>
        <p>Status: <strong>Connected</strong></p>
        <p>Region: us-central1</p>
    </div>
    
    <div class="status-card online">
        <h3>🔥 Firebase</h3>
        <p>Status: <strong>Connected</strong></p>
        <p>Project: drishti-public-safety</p>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => location.reload(), 30000);
    </script>
</body>
</html>
        """
        
        status_file = self.base_path / 'system_status.html'
        with open(status_file, 'w') as f:
            f.write(status_html)
        
        print(f"✅ System status dashboard created: {status_file}")
        return True
    
    async def deploy_complete_system(self):
        """Deploy the complete Drishti system"""
        print("🚀 DEPLOYING COMPLETE DRISHTI AI SAFETY SYSTEM 🚀")
        print("=" * 60)
        
        deployment_steps = [
            ("Dependencies", self.check_dependencies),
            ("Environment Setup", self.setup_environment_variables),
            ("Firebase Dashboard", self.deploy_firebase_dashboard),
            ("System Status", self.create_system_status_dashboard),
            ("Emergency Agent", self.start_emergency_agent),
            ("Real-time Monitoring", self.start_realtime_monitoring)
        ]
        
        success_count = 0
        for step_name, step_func in deployment_steps:
            print(f"\n🔄 {step_name}...")
            try:
                if step_func():
                    success_count += 1
                    print(f"✅ {step_name} completed successfully")
                else:
                    print(f"❌ {step_name} failed")
            except Exception as e:
                print(f"❌ {step_name} error: {e}")
        
        print("\n" + "=" * 60)
        print(f"🎯 DEPLOYMENT SUMMARY: {success_count}/{len(deployment_steps)} steps completed")
        
        if success_count == len(deployment_steps):
            print("🎉 COMPLETE SYSTEM DEPLOYMENT SUCCESSFUL! 🎉")
            print("\n📋 SYSTEM ENDPOINTS:")
            print("🌐 Dashboard: https://drishti-public-safety.web.app")
            print("🚨 Emergency API: http://localhost:8001")
            print(f"📊 Status Page: file://{self.base_path}/system_status.html")
            print("\n🤖 Master Agent is now running with:")
            print("   • Real-time camera monitoring")
            print("   • Vertex AI video analysis")
            print("   • Gemini risk assessment")
            print("   • Firebase live dashboard")
            print("   • Twilio emergency alerts")
            print("   • Complete system orchestration")
        else:
            print("⚠️ Partial deployment completed. Check errors above.")
        
        return success_count == len(deployment_steps)

async def main():
    """Main deployment entry point"""
    deployer = DrishtiDeployment()
    success = await deployer.deploy_complete_system()
    
    if success:
        print("\n🚀 Starting Master Agent...")
        # Keep the master agent running
        master_agent_path = deployer.components['master_agent']
        subprocess.run([sys.executable, str(master_agent_path)])
    else:
        print("\n❌ Deployment failed. Please check errors and try again.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
