# 🎨 Virtual Try-On System

AI-powered virtual try-on system using OpenAI's image generation models. Create realistic try-on experiences by generating custom models and merging them with clothing items through a sophisticated multi-agent workflow.

## ✨ Key Features

- **🤖 Multi-Agent Architecture**: Three specialized AI agents working together
  - **ModelDescriptionAgent**: Generates detailed model descriptions from parameters
  - **ModelGenerationAgent**: Creates model images from descriptions
  - **ImageMergeAgent**: Seamlessly merges models with clothing items
  - **ClothingCheckAgent**: Validates uploaded clothing images

- **🎯 Customizable Models**: Full control over model appearance
  - Gender, age, nationality specifications
  - Height and weight parameters
  - Camera settings (full-body/half-body, front/side angles)
  - Custom pose and scene descriptions

- **🚀 Complete Workflow**: End-to-end virtual try-on process
  - Automatic clothing validation
  - Step-by-step generation with progress tracking
  - Real-time status updates
  - High-quality output images

- **🌐 Network Ready**: Built for deployment and sharing
  - LAN/network accessible
  - Modern React frontend
  - FastAPI backend with comprehensive endpoints
  - One-click startup system

## 🏗️ System Architecture

```
Frontend (React - Port 3000)
    ↓ HTTP Requests
Backend (FastAPI - Port 8000)
    ↓ Agent Coordination
Function Agents Module
├── ModelDescriptionAgent
├── ModelGenerationAgent  
├── ImageMergeAgent
└── ClothingCheckAgent
    ↓ OpenAI API
OpenAI Image Generation
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8+
- Node.js & npm
- OpenAI API key

### 2. Environment Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
npm install

# Configure OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
# or create a .env file with:
# OPENAI_API_KEY=your-api-key-here
```

### 3. Launch Application
```bash
# One-click startup (recommended)
python3 start_system.py

# Manual startup:
# Terminal 1: Backend
python3 api_server.py
# Terminal 2: Frontend  
npm start
```

### 4. Access Application
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎯 How to Use

### Web Interface
1. **Upload Clothing**: Select a clear image of clothing item (no model)
2. **Configure Model**: Set gender, age, nationality, height, weight
3. **Customize Camera**: Choose shot type (full/half body) and angle
4. **Add Descriptions**: Optional pose and scene descriptions
5. **Generate**: Watch the three-step AI workflow
6. **Download**: Get your virtual try-on result

### API Usage
```javascript
// Example: Generate virtual try-on
const response = await fetch('http://localhost:8000/api/generate-model', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    clothingImage: base64ImageData,
    gender: 'female',
    age: 25,
    nationality: 'Chinese',
    height: 170,
    weight: 60,
    camera: {
      shot_type: 'full_body',
      angle: 'front'
    },
    actionDescription: 'confident modeling pose',
    sceneDescription: 'professional studio background'
  })
});

const result = await response.json();
// Generated image path: result.result.generated_image.image_path
```

### Python SDK
```python
from function_agents import generate_complete_tryon

# Configure model parameters
model_specs = {
    'gender': 'female',
    'age': 25,
    'nationality': 'Chinese', 
    'height': 170,
    'weight': 60,
    'camera': {
        'shot_type': 'full_body',
        'angle': 'front'
    },
    'action_description': 'confident pose',
    'scene_description': 'studio background'
}

# Generate try-on image
result_path = generate_complete_tryon(
    clothing_image_path="path/to/clothing.jpg",
    model_specs=model_specs
)

print(f"Generated: {result_path}")
```

## 📡 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/generate-model` | POST | Complete virtual try-on workflow |
| `/api/generate-step-by-step` | POST | Step-by-step generation with progress |
| `/api/generate-model-only` | POST | Generate model without clothing |
| `/api/check-clothing` | POST | Validate clothing image |
| `/api/merge-clothing-only` | POST | Merge existing model with clothing |
| `/api/status` | GET | System health check |
| `/imgs/{filename}` | GET | Serve generated images |

### Request Parameters

```json
{
  "clothingImage": "base64_encoded_image_data",
  "gender": "female|male",
  "age": 18-80,
  "nationality": "Chinese|American|European|etc",
  "height": 150-200,
  "weight": 40-120,
  "camera": {
    "shot_type": "full_body|half_body",
    "angle": "front|side"
  },
  "actionDescription": "optional pose description",
  "sceneDescription": "optional background description"
}
```

## 📁 Project Structure

```
taobao/
├── api_server.py              # FastAPI backend server
├── start_system.py           # One-click startup script
├── function_agents/          # AI agent modules
│   ├── __init__.py          # Main workflow orchestration
│   ├── model_description_agent.py
│   ├── model_generation_agent.py
│   ├── image_merge_agent.py
│   └── check_single_cloth.py
├── src/                      # React frontend
│   ├── App.js               # Main React component
│   ├── App.css              # Styling
│   └── index.js             # Entry point
├── public/                   # Static frontend assets
├── imgs/                     # Generated images storage
├── uploads/                  # Temporary upload storage
├── requirements.txt          # Python dependencies
├── package.json             # Node.js dependencies
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your-openai-api-key
HOST=0.0.0.0                # Network binding
BACKEND_PORT=8000           # Backend port
FRONTEND_PORT=3000          # Frontend port
```

### Customization Options
- **Image Quality**: Modify size and compression in `api_server.py`
- **Generation Parameters**: Adjust prompts in agent modules
- **UI Styling**: Update `src/App.css` for frontend appearance
- **Timeout Settings**: Configure request timeouts in startup script

## 🚀 Deployment

### Local Network Access
The system automatically binds to `0.0.0.0`, making it accessible from any device on your network at:
- `http://YOUR_LOCAL_IP:3000` (frontend)
- `http://YOUR_LOCAL_IP:8000` (backend)

### Production Deployment
1. **Build Frontend**: `npm run build`
2. **Configure Reverse Proxy**: Nginx/Apache configuration
3. **Environment Setup**: Production environment variables
4. **Process Management**: PM2 or systemd services

## 🔍 Troubleshooting

### Common Issues
- **Port Conflicts**: Ensure ports 3000 and 8000 are available
- **API Key Issues**: Verify OpenAI API key in environment
- **Image Generation Fails**: Check network connection and API quotas
- **Missing Dependencies**: Run installation commands again

### Debug Mode
```bash
# Enable verbose logging
export DEBUG=1
python3 api_server.py
```

### Performance Optimization
- **Concurrent Requests**: Configured ThreadPoolExecutor for CPU-intensive tasks
- **Image Processing**: Optimized PIL operations with memory management
- **Caching**: Implement Redis for frequently accessed data

## 📊 System Requirements

### Minimum Requirements
- **CPU**: 2+ cores
- **RAM**: 4GB+ 
- **Storage**: 2GB+ free space
- **Network**: Stable internet for OpenAI API

### Recommended Configuration
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 10GB+ SSD
- **Network**: High-speed broadband

## 🎉 Features Highlight

- ✅ **Multi-Agent Workflow**: Sophisticated AI coordination
- ✅ **Real-time Progress**: Step-by-step generation tracking
- ✅ **Input Validation**: Automatic clothing image verification
- ✅ **Network Ready**: LAN/WAN accessible deployment
- ✅ **Modern UI**: Responsive React interface
- ✅ **RESTful API**: Clean, documented endpoints
- ✅ **One-Click Setup**: Automated dependency installation
- ✅ **High Quality**: Professional fashion photography output

---

**🚀 Ready to create stunning virtual try-on experiences!** 