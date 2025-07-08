import base64
import os
from openai import OpenAI
from PIL import Image
from io import BytesIO
import uuid
from typing import Optional, Dict
from pydantic import BaseModel, Field

class GenerationResult(BaseModel):
    """Model generation result"""
    image_path: str = Field(..., description="Path to the generated image")

class ModelGenerationAgent:
    def __init__(self):
        """Initialize model generation agent with OpenAI client"""
        self.client = OpenAI()
        
        # Ensure output directory exists
        os.makedirs('imgs', exist_ok=True)
    
    def generate_model_image(self, 
                           prompt: str, 
                           output_path: Optional[str] = None) -> GenerationResult:
        """
        Generate model image from optimized prompt
        
        Args:
            prompt: Pre-optimized prompt from ModelDescriptionAgent
            output_path: Output path, auto-generated if None
            
        Returns:
            GenerationResult with image path
        """
        
        try:
            print(f"🎨 Generating model image with prompt...")
            
            # Generate image using OpenAI API
            result = self.client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1536",
                quality="high"
            )
            
            # Set output path
            if output_path is None:
                model_filename = f"model_{uuid.uuid4().hex[:8]}.jpg"
                output_path = os.path.join('imgs', model_filename)
            
            # Save image
            if result.data and result.data[0].url:
                self._download_and_save_image(result.data[0].url, output_path)
            elif result.data and result.data[0].b64_json:
                self._save_image_from_base64(result.data[0].b64_json, output_path)
            else:
                raise ValueError("Failed to generate model image - no data received")
            
            print(f"✅ Model image saved: {output_path}")
            
            return GenerationResult(image_path=output_path)
                
        except Exception as e:
            print(f"❌ Model generation failed: {e}")
            raise e
    
    def _download_and_save_image(self, image_url: str, output_path: str) -> None:
        """Download and save image from URL"""
        import requests
        
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save image with high quality
            image.save(output_path, format="JPEG", quality=95)
            
        except Exception as e:
            raise ValueError(f"Failed to download and save image: {e}")
    
    def _save_image_from_base64(self, base64_data: str, output_path: str) -> None:
        """Save image from base64 data"""
        try:
            # Decode base64 data
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB format
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Save image with high quality
            image.save(output_path, format="JPEG", quality=95)
            
        except Exception as e:
            raise ValueError(f"Failed to save image from base64: {e}")

    def get_generation_status(self) -> Dict:
        """Get current generation agent status"""
        return {
            "agent_type": "ModelGenerationAgent",
            "status": "ready",
            "input_type": "optimized_prompt_string",
            "features": [
                "single_model_generation",
                "high_quality_output", 
                "ready_for_clothing_merge"
            ],
            "model": "gpt-image-1",
            "output_directory": "imgs/"
        }

# Simple factory function
def create_model_generation_agent() -> ModelGenerationAgent:
    """Create model generation agent instance"""
    return ModelGenerationAgent()

# Main interface
def generate_model_from_prompt(prompt: str, 
                             output_path: Optional[str] = None) -> GenerationResult:
    """
    Generate model image from optimized prompt
    
    Args:
        prompt: Pre-optimized prompt string from ModelDescriptionAgent
        output_path: Output path, auto-generated if None
        
    Returns:
        GenerationResult with image path
    """
    agent = create_model_generation_agent()
    return agent.generate_model_image(prompt, output_path)

