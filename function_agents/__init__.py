"""
Function Agents Module - Virtual Try-on System

Contains three specialized agents:
1. ModelDescriptionAgent - Generate model descriptions
2. ModelGenerationAgent - Generate model images
3. ImageMergeAgent - Merge model and clothing images

Usage:
from function_agents import generate_complete_tryon

result = generate_complete_tryon(
    clothing_image_path="path/to/clothing.jpg",
    model_specs={
        "gender": "female",
        "age": 25,
        "nationality": "Chinese",
        "height": 170,
        "weight": 60,
        "camera": {"shot_type": "full_body", "angle": "front"},
        "action_description": "自信的时尚姿势",
        "scene_description": "简洁的工作室背景"
    }
)
"""

from typing import Dict, Optional
import os

# Import all agents
from .model_description_agent import create_model_description_agent, generate_model_description
from .model_generation_agent import create_model_generation_agent, generate_model_from_prompt
from .image_merge_agent import merge_model_with_clothing
from .check_single_cloth import check_cloth_validity, check_single_cloth


def generate_complete_tryon(clothing_image_path: str,
                          model_specs: Dict,
                          output_path: Optional[str] = None) -> str:
    """
    Complete virtual try-on workflow integrating all three agents
    
    Args:
        clothing_image_path: Path to clothing image
        model_specs: Model specification parameters
        output_path: Output path for final image
        
    Returns:
        Path to the generated try-on image
    """
    print("🚀 Starting complete virtual try-on workflow...")
    
    try:
        # Separate parameters: basic model info and camera/action/scene parameters
        basic_model_specs = {
            'gender': model_specs.get('gender', 'female'),
            'age': model_specs.get('age', 25),
            'nationality': model_specs.get('nationality', 'Chinese'),
            'height': model_specs.get('height', 170),
            'weight': model_specs.get('weight', 60)
        }
        
        # Extract camera and description parameters
        camera_settings = model_specs.get('camera', {})
        shot_type = camera_settings.get('shot_type', 'full_body')
        angle = camera_settings.get('angle', 'front')
        pose_description = model_specs.get('action_description', '')
        scene_description = model_specs.get('scene_description', '')
        
        # Step 1: Generate model description
        print("📝 Step 1: Generating model description...")
        description = generate_model_description(basic_model_specs)
        print("✅ Description completed")
        
        # Step 2: Generate model image
        print("🎨 Step 2: Generating model image...")
        model_result = generate_model_from_prompt(description)
        print(f"✅ Model image completed: {model_result.image_path}")
        
        # Step 3: Merge images
        print("👕 Step 3: Merging model with clothing...")
        merge_result = merge_model_with_clothing(
            model_result.image_path,
            clothing_image_path,
            shot_type=shot_type,
            angle=angle,
            pose_description=pose_description,
            scene_description=scene_description
        )
        print(f"✅ Merge completed: {merge_result}")
        
        print("🎉 Workflow finished!")
        return merge_result
        
    except Exception as e:
        print(f"❌ Virtual try-on workflow failed: {e}")
        raise e


def get_agents_status() -> Dict:
    """Get status of all agents"""
    try:
        return {
            "model_description_agent": {"status": "ready"},
            "model_generation_agent": {"status": "ready"},
            "image_merge_agent": {"status": "ready"},
            "integrated_workflow": {"status": "ready"}
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed: {e}"}


# Export main functions
__all__ = [
    'generate_complete_tryon',
    'get_agents_status',
    'create_model_description_agent',
    'create_model_generation_agent',
    'generate_model_description',
    'generate_model_from_prompt',
    'merge_model_with_clothing',
    'check_cloth_validity',
    'check_single_cloth'
] 