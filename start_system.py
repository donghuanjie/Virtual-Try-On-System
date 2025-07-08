#!/usr/bin/env python3
"""
Virtual Try-On System Startup Script
One-click startup for frontend and backend services
"""

import subprocess
import sys
import os
import time
import webbrowser
import socket
from threading import Thread

def get_local_ip():
    """Get local LAN IP address"""
    try:
        # Create a UDP socket connection to external address to get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use Google DNS as target (won't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        return "127.0.0.1"

def check_nodejs():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False

def check_npm():
    """Check if npm is installed"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
            return True
        else:
            print("❌ npm not installed or not in PATH")
            return False
    except FileNotFoundError:
        print("❌ npm not installed")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies"""
    print("📦 Installing frontend dependencies...")
    try:
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Frontend dependencies installed successfully")
            return True
        else:
            print(f"❌ Frontend dependencies installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing frontend dependencies: {e}")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python dependencies installed successfully")
            return True
        else:
            print(f"❌ Python dependencies installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing Python dependencies: {e}")
        return False

def start_backend():
    """Start backend service"""
    print("🚀 Starting backend service...")
    try:
        # Start Flask server
        process = subprocess.Popen([sys.executable, 'api_server.py'])
        return process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start frontend service with network access"""
    print("🌐 Starting frontend service...")
    try:
        # Start React development server with network access
        env = os.environ.copy()
        env['BROWSER'] = 'none'  # Disable automatic browser opening
        env['HOST'] = '0.0.0.0'  # Bind to all network interfaces
        process = subprocess.Popen(['npm', 'start'], env=env)
        return process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def wait_for_backend(local_ip):
    """Wait for backend service to start"""
    import requests
    print("⏳ Waiting for backend service to start...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f'http://{local_ip}:8000/api/status', timeout=2)
            if response.status_code == 200:
                print("✅ Backend service is ready")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"⏳ Waiting... ({i+1}/30)")
    
    print("❌ Backend service startup timeout")
    return False

def wait_for_frontend(local_ip):
    """Wait for frontend service to start"""
    import requests
    print("⏳ Waiting for frontend service to start...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f'http://{local_ip}:3000', timeout=2)
            if response.status_code == 200:
                print("✅ Frontend service is ready")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0:
            print(f"⏳ Waiting... ({i+1}/30)")
    
    print("❌ Frontend service startup timeout")
    return False

def open_browser(local_ip):
    """Open browser with local IP"""
    print("🌐 Opening browser...")
    webbrowser.open(f'http://{local_ip}:3000')

def main():
    """Main function"""
    print("🎨 Virtual Try-On System Launcher")
    print("=" * 50)
    
    # Get local IP address
    local_ip = get_local_ip()
    print(f"🌐 Local IP Address: {local_ip}")
    
    # Check environment
    print("🔍 Checking runtime environment...")
    if not check_nodejs():
        print("Please install Node.js first: https://nodejs.org/")
        return
    
    if not check_npm():
        print("Please ensure npm is properly installed")
        return
    
    # Check project files
    required_files = ['api_server.py', 'package.json', 'requirements.txt']
    required_dirs = ['function_agents', 'src']
    agent_files = [
        'function_agents/model_description_agent.py',
        'function_agents/model_generation_agent.py', 
        'function_agents/image_merge_agent.py'
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
    missing_agents = [f for f in agent_files if not os.path.exists(f)]
    
    if missing_files or missing_dirs or missing_agents:
        all_missing = missing_files + missing_dirs + missing_agents
        print(f"❌ Missing project files: {', '.join(all_missing)}")
        return
    
    print("✅ Environment check passed")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_python_dependencies():
        return
    
    if not os.path.exists('node_modules'):
        if not install_frontend_dependencies():
            return
    else:
        print("✅ Frontend dependencies already exist")
    
    print("\n🚀 Starting services...")
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait for backend to start
    if not wait_for_backend(local_ip):
        backend_process.terminate()
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    # Wait for frontend to start
    if wait_for_frontend(local_ip):
        # Automatically open browser after frontend starts successfully
        time.sleep(2)  # Wait a bit to ensure frontend is fully loaded
        open_browser(local_ip)
    
    print("\n🎉 System startup successful!")
    print("=" * 50)
    print("📍 Backend API:")
    print(f"   🏠 Local: http://localhost:8000")
    print(f"   🌐 Network: http://{local_ip}:8000")
    print("\n🌐 Frontend Web:")
    print(f"   🏠 Local: http://localhost:3000")
    print(f"   🌐 Network: http://{local_ip}:3000")
    print("\n📲 Network Access Information:")
    print(f"   Other devices can access: http://{local_ip}:3000")
    print("   Ensure firewall allows access to ports 3000 and 8000")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Wait for user interrupt
        backend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 