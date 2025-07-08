from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
import base64
import time
import asyncio
import json
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from function_agents import generate_complete_tryon, get_agents_status
from function_agents.check_single_cloth import check_cloth_validity
import datetime

# Create FastAPI application
app = FastAPI(title="Virtual Try-On System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('imgs', exist_ok=True)

# Create thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

# Pydantic model definitions
class CameraSettings(BaseModel):
    """Camera parameter settings"""
    shot_type: Optional[str] = "full_body"  # "full_body" or "half_body"
    angle: Optional[str] = "front"  # "front" or "side"

class GenerateModelRequest(BaseModel):
    clothingImage: str
    gender: Optional[str] = "female"
    age: Optional[int] = 25
    nationality: Optional[str] = "Chinese"
    height: Optional[int] = 170
    weight: Optional[int] = 60
    actionDescription: Optional[str] = None
    sceneDescription: Optional[str] = None
    camera: Optional[CameraSettings] = CameraSettings()

class GenerateModelOnlyRequest(BaseModel):
    gender: Optional[str] = "female"
    age: Optional[int] = 25
    nationality: Optional[str] = "Chinese"
    height: Optional[int] = 170
    weight: Optional[int] = 60
    actionDescription: Optional[str] = None
    sceneDescription: Optional[str] = None
    camera: Optional[CameraSettings] = CameraSettings()

class MergeClothingRequest(BaseModel):
    clothingImage: str
    modelImagePath: str
    shot_type: Optional[str] = "全身"
    angle: Optional[str] = "正面"
    pose_description: Optional[str] = "自然站立姿势"
    scene_description: Optional[str] = "简约工作室背景"

class ClothingCheckRequest(BaseModel):
    clothingImage: str

# Helper functions: Process image data
def process_image_data(image_data: str) -> str:
    """Process base64 image data and save as temporary file"""
    if image_data.startswith('data:image'):
        image_data = image_data.split(',')[1]
    
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    
    # Convert RGBA to RGB
    if image.mode == 'RGBA':
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Create temporary file
    unique_filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    image.save(filepath, format="JPEG", quality=90)
    
    return filepath

def process_model_params(data: dict) -> dict:
    """Process model parameters"""
    model_params = {
        'gender': data.get('gender', 'female'),
        'age': int(data.get('age', 25)),
        'nationality': data.get('nationality', 'Chinese'),
        'height': int(data.get('height', 170)),
        'weight': int(data.get('weight', 60))
    }
    
    # Process camera parameters
    camera_settings = data.get('camera', {})
    if camera_settings:
        model_params['camera'] = {
            'shot_type': camera_settings.get('shot_type', 'full_body'),
            'angle': camera_settings.get('angle', 'front')
        }
    else:
        # Default camera settings
        model_params['camera'] = {
            'shot_type': 'full_body',
            'angle': 'front'
        }
    
    if data.get('actionDescription'):
        model_params['action_description'] = data['actionDescription']
    if data.get('sceneDescription'):
        model_params['scene_description'] = data['sceneDescription']
    
    return model_params

def cleanup_temp_file(filepath: str):
    """Clean up temporary files"""
    if os.path.exists(filepath):
        os.remove(filepath)

def extract_image_path(result_string: str) -> str:
    """Extract actual image path from agent result string"""
    import re
    
    # 如果已经是简单的文件路径，直接返回
    if result_string.startswith('imgs/') and result_string.endswith('.jpg'):
        return result_string
    
    # 尝试从包含文本的字符串中提取路径
    # 匹配模式如：imgs/tryon_f6026f8c.jpg
    patterns = [
        r'imgs/[a-zA-Z0-9_]+\.jpg',  # 标准的imgs/文件名.jpg格式
        r'[a-zA-Z0-9_/]+\.jpg',     # 任何以.jpg结尾的路径
    ]
    
    for pattern in patterns:
        match = re.search(pattern, result_string)
        if match:
            path = match.group()
            # 验证文件是否真的存在
            if os.path.exists(path):
                return path
    
    # 如果都没找到，返回原字符串（让后续错误处理来处理）
    return result_string

def get_image_info(image_path: str) -> dict:
    """Get image information"""
    if os.path.exists(image_path):
        file_size = os.path.getsize(image_path)
        filename = os.path.basename(image_path)
        timestamp = int(time.time() * 1000)
        
        return {
            'success': True,
            'image_path': image_path,
            'filename': filename,
            'file_size_kb': round(file_size / 1024, 2),
            'timestamp': timestamp,
            'image_url': f"/imgs/{filename}?t={timestamp}"
        }
    else:
        return {
            'success': False,
            'error': 'Image not found'
        }

# Async wrapper function for CPU-intensive tasks
async def async_generate_complete_tryon(filepath: str, model_params: dict) -> str:
    """Asynchronously execute complete virtual try-on generation"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, generate_complete_tryon, filepath, model_params)



# Main API endpoints
@app.post("/api/generate-model")
async def generate_model(request: GenerateModelRequest):
    """
    Main virtual try-on generation endpoint
    Accepts JSON data containing base64 encoded clothing image and model parameters
    """
    try:
        # Process image data
        filepath = process_image_data(request.clothingImage)
        
        # Process model parameters
        model_params = process_model_params(request.dict())
        
        # Execute AI generation asynchronously
        print("🚀 Starting virtual try-on generation with new agents...")
        result_path = await async_generate_complete_tryon(filepath, model_params)
        
        # Clean up temporary files
        cleanup_temp_file(filepath)
        
        # Get generated image information
        image_info = get_image_info(result_path)
        
        if image_info['success']:
            return {
                'success': True,
                'result': {
                    'generated_image': image_info
                },
                'message': 'Virtual try-on image generated successfully with new agents'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    'success': False,
                    'result': {
                        'generated_image': image_info
                    },
                    'error': 'Generated image file not found'
                }
            )
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")



@app.post("/api/generate-step-by-step")
async def generate_step_by_step(request: GenerateModelRequest):
    """
    Step-by-step virtual try-on generation with intermediate results
    """
    try:
        # Process image data
        filepath = process_image_data(request.clothingImage)
        
        # Process model parameters
        model_params = process_model_params(request.dict())
        
        print("🚀 Starting step-by-step virtual try-on generation...")
        
        # Async import functions
        from function_agents import (
            generate_model_description,
            merge_model_with_clothing
        )
        from function_agents.model_generation_agent import generate_model_from_prompt
        
        # Use thread pool for CPU-intensive tasks
        loop = asyncio.get_event_loop()
        
        # Step 1: Generate model description
        print("📝 Step 1: Generating model description...")
        description = await loop.run_in_executor(executor, generate_model_description, model_params)
        
        # Step 2: Generate model image
        print("🎨 Step 2: Generating model image...")
        model_result = await loop.run_in_executor(executor, generate_model_from_prompt, description)
        
        # Check if model image exists
        if not os.path.exists(model_result.image_path):
            raise Exception(f"Model image not generated: {model_result.image_path}")
        
        # Step 3: Merge images with camera parameters
        print("👕 Step 3: Merging model with clothing...")
        # Extract camera and description parameters from model_params
        camera_settings = model_params.get('camera', {})
        shot_type = '全身' if camera_settings.get('shot_type', 'full_body') == 'full_body' else '半身'
        angle = '正面' if camera_settings.get('angle', 'front') == 'front' else '侧面'
        pose_description = model_params.get('action_description', '自然站立姿势')
        scene_description = model_params.get('scene_description', '简约工作室背景')
        
        final_result = await loop.run_in_executor(
            executor, 
            merge_model_with_clothing, 
            model_result.image_path, 
            filepath,
            shot_type,
            angle,
            pose_description,
            scene_description
        )
        
        # Clean up temporary files
        cleanup_temp_file(filepath)
        
        # Extract actual image path from agent result
        final_image_path = extract_image_path(final_result)
        
        # Get image information
        model_info = get_image_info(model_result.image_path)
        final_info = get_image_info(final_image_path)
        
        if final_info['success']:
            return {
                'success': True,
                'result': {
                    'model_image': model_info,
                    'final_image': final_info
                },
                'message': 'Step-by-step generation completed successfully'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    'success': False,
                    'error': 'Final image generation failed'
                }
            )
        
    except Exception as e:
        print(f"Step-by-step generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e)
            }
        )

@app.post("/api/generate-model-only")
async def generate_model_only(request: GenerateModelOnlyRequest):
    """
    Generate model image only, without clothing merge
    """
    try:
        # Process model parameters
        model_params = process_model_params(request.dict())
        
        print("🚀 Starting model-only generation...")
        
        from function_agents import generate_model_description
        from function_agents.model_generation_agent import generate_model_from_prompt
        
        # Use thread pool for CPU-intensive tasks
        loop = asyncio.get_event_loop()
        
        # Step 1: Generate model description
        print("📝 Step 1: Generating model description...")
        description = await loop.run_in_executor(executor, generate_model_description, model_params)
        
        # Step 2: Generate model image
        print("🎨 Step 2: Generating model image...")
        model_result = await loop.run_in_executor(executor, generate_model_from_prompt, description)
        
        # Check if model image exists
        if not os.path.exists(model_result.image_path):
            raise Exception(f"Model image not generated: {model_result.image_path}")
        
        # Get image information
        model_info = get_image_info(model_result.image_path)
        
        return {
            'success': True,
            'result': {
                'model_image': model_info
            },
            'message': 'Model generation completed successfully'
        }
        
    except Exception as e:
        print(f"Model generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e)
            }
        )

@app.post("/api/check-clothing")
async def check_clothing(request: ClothingCheckRequest):
    """
    Clothing validation endpoint
    Checks if the uploaded image contains exactly one piece of top clothing
    """
    try:
        # Process image data
        clothing_filepath = process_image_data(request.clothingImage)
        
        # Check clothing validity
        check_result = check_cloth_validity(clothing_filepath)
        
        # Clean up temporary file
        cleanup_temp_file(clothing_filepath)
        
        # Return result
        return {
            "success": True,
            "result": check_result
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Clothing validation failed: {str(e)}"
            }
        )

@app.post("/api/merge-clothing-only")
async def merge_clothing_only(request: MergeClothingRequest):
    """
    Perform image merge only, requires model image path and clothing image
    """
    try:
        # Process clothing image data
        filepath = process_image_data(request.clothingImage)
        
        model_image_path = request.modelImagePath
        
        print("👕 Starting clothing merge...")
        
        from function_agents import merge_model_with_clothing
        
        # Use thread pool for merge task with all parameters
        loop = asyncio.get_event_loop()
        final_result = await loop.run_in_executor(
            executor, 
            merge_model_with_clothing, 
            model_image_path, 
            filepath,
            request.shot_type or "全身",
            request.angle or "正面",
            request.pose_description or "自然站立姿势",
            request.scene_description or "简约工作室背景"
        )
        
        # Clean up temporary files
        cleanup_temp_file(filepath)
        
        # Extract actual image path from agent result
        final_image_path = extract_image_path(final_result)
        
        # Get final image information
        final_info = get_image_info(final_image_path)
        
        if final_info['success']:
            return {
                'success': True,
                'result': {
                    'final_image': final_info
                },
                'message': 'Clothing merge completed successfully'
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    'success': False,
                    'error': 'Image merge failed'
                }
            )
        
    except Exception as e:
        print(f"Clothing merge error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e)
            }
        )

# File service endpoints
@app.get("/api/get-image/{filename:path}")
async def get_image(filename: str):
    """Get generated image"""
    try:
        if os.path.exists(filename):
            return FileResponse(filename, media_type='image/jpeg')
        else:
            raise HTTPException(status_code=404, detail={'error': 'Image not found'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})

@app.get("/imgs/{filename}")
async def serve_imgs(filename: str):
    """Serve images from imgs folder"""
    try:
        img_path = os.path.join('imgs', filename)
        if os.path.exists(img_path):
            return FileResponse(img_path, media_type='image/jpeg')
        else:
            raise HTTPException(status_code=404, detail={'error': 'Image not found'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})

# Status and test endpoints
@app.get("/api/status")
async def status():
    """Check API status - updated to use new agents"""
    try:
        return get_agents_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})

@app.get("/api/test-agents")
async def test_agents():
    """Test if agents are working properly"""
    try:
        print("🔍 Testing agents functionality...")
        
        # Use thread pool for status check
        loop = asyncio.get_event_loop()
        status_result = await loop.run_in_executor(executor, get_agents_status)
        
        return {
            'success': True,
            'message': 'Agents test completed',
            'agents_status': status_result,
            'test_time': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Agents test error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Agents test failed'
            }
        )

# Root path
@app.get("/")
async def root():
    """Root path information"""
    return {
        "message": "Virtual Try-On System API",
        "version": "1.0.0",
        "endpoints": [
            "/api/generate-model",
            "/api/generate-step-by-step",
            "/api/generate-model-only",
            "/api/check-clothing",
            "/api/merge-clothing-only",
            "/api/status",
            "/api/test-agents"
        ]
    }

# General file service (placed last to avoid matching conflicts)
@app.get("/{filename:path}")
async def serve_static_files(filename: str):
    """Serve static files for accessing generated images"""
    # Skip known API paths and root path
    if filename == "" or filename.startswith("api/") or filename.startswith("docs") or filename.startswith("openapi.json"):
        raise HTTPException(status_code=404, detail={'error': 'Not found'})
    
    try:
        if os.path.exists(filename):
            return FileResponse(filename, media_type='image/jpeg')
        else:
            raise HTTPException(status_code=404, detail={'error': 'File not found'})
    except Exception as e:
        raise HTTPException(status_code=500, detail={'error': str(e)})

if __name__ == '__main__':
    import uvicorn
    
    print("🚀 Starting virtual try-on system backend service with FastAPI...")
    print("📍 API URL: http://localhost:8000")
    print("🎨 Main endpoint: /api/generate-model")
    print("⚡ Step-by-step endpoint: /api/generate-step-by-step")
    print("📷 Image access: /imgs/<filename> or /<image_path>")
    print("🔍 Test endpoint: /api/test-agents")
    print("📊 Status endpoint: /api/status")
    print("\n💡 Three-agent process:")
    print("   1. ModelDescriptionAgent - Generate model description")
    print("   2. ModelGenerationAgent - Generate model image")
    print("   3. ImageMergeAgent - Merge model with clothing")
    print("📁 All images stored in: imgs/ folder")
    print("✨ FastAPI with async support for better concurrency!")
    print("🚀 Auto-reload enabled for development")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=4,  # Development mode uses 1 worker with reload
        log_level="info"
    ) 