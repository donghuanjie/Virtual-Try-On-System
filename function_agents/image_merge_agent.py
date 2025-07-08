import base64
import os
import uuid
import asyncio
from openai import OpenAI
from PIL import Image
from io import BytesIO
from typing import Optional
from agents import Agent, Runner, function_tool

# Initialize OpenAI client
client = OpenAI()

@function_tool
def image_merge(img1: str, img2: str, prompt: str) -> str:
    """
    Merge two images using OpenAI's image edit API
    """
    try:
        print(f"📝 Generated prompt: {prompt}")
        
        if not os.path.exists(img1) or not os.path.exists(img2):
            raise FileNotFoundError("One or both image paths do not exist")

        with open(img1, "rb") as img1_file, open(img2, "rb") as img2_file:
            result_edit = client.images.edit(
                model="gpt-image-1",
                image=[img1_file, img2_file], 
                prompt=prompt,
                size="1024x1536",
                quality="high"
            )

            # Use consistent 8-character UUID naming, same as model image naming convention
            unique_id = uuid.uuid4().hex[:8]
            output_filename = f"tryon_{unique_id}.jpg"
            output_dir = "imgs"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_filename)

            if result_edit.data and result_edit.data[0].b64_json:
                image_base64 = result_edit.data[0].b64_json
                image_bytes = base64.b64decode(image_base64)
                
                image = Image.open(BytesIO(image_bytes))
                
                # Handle RGBA format conversion only
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                
                image.save(output_path, format="JPEG", quality=90, optimize=True)
                return output_path
            else:
                raise ValueError("No image data received from API")

    except Exception as e:
        raise ValueError(f"Image merge failed: {str(e)}")

# Translation agent
english_translate_agent = Agent(
    name="Fashion English Translator",
    instructions="""
You are a professional Chinese-English translator specialized in fashion photography and modeling descriptions.
Task: Accurately translate Chinese text into natural, fluent English suitable for fashion photography and AI image generation.
Rules:
1. Only translate the Chinese parts, keep English parts unchanged
2. Make translations natural and suitable for fashion photography descriptions
3. Keep the translation concise and descriptive
4. Focus on visual and fashion-related terminology
""",
    model="gpt-4o"
)

# Main orchestrator agent
agent = Agent(
    name="Virtual Try-on Agent",
    instructions="""
You are a Virtual Try-on Agent that prepares professional prompts for GPT-image-1 to generate high-quality fashion model images for virtual try-on.

Task:
Based on 4 user inputs:
- shot_type: either "full_body" or "half_body"
- angle: either "front" or "side"
- pose_description: short text in Chinese or English
- scene_description: short text in Chinese or English

Please follow these steps:

1. If pose_description or scene_description contains Chinese characters, use the "translate_to_english" tool to translate them into fluent English suitable for professional image generation. Do NOT alter the original meaning.

2. Construct a **final 3–4 sentence prompt** describing the image in this exact structure:

   - Sentence 1: Describe the shot type (e.g., "This is a full body fashion photograph of a model wearing the uploaded clothing.")
   - Sentence 2: Describe the camera angle (e.g., "The model is positioned facing the camera." or "The model is positioned at a side-facing angle.")
   - Sentence 3: Insert the pose_description in fluent English, keeping it natural, visual, and fashion-relevant.
   - Sentence 4 (optional): If provided, insert the scene_description in fluent English, focusing on clean studio setups or visually coherent fashion backgrounds.

Style rules:
- Use natural, vivid fashion language
- Avoid photography jargon like “lens” or “camera”
- Do NOT mention the AI, tool, or uploaded image
- Do NOT add any explanatory or filler content

3. After constructing the 3–4 sentence prompt, call the `image_merge` tool using:
   - img1: the model image
   - img2: the clothing image
   - prompt: the 3–4 sentence full prompt you just created

4. Only return the file path from `image_merge`. Do not output anything else.

Example prompt:
"This is a full body fashion photograph of a model wearing the uploaded clothing. The model is positioned facing the camera. She stands confidently with hands at her sides and a soft smile. The background is a clean white studio with soft professional lighting."
""",
    tools=[
        english_translate_agent.as_tool(
            tool_name="translate_to_english",
            tool_description="Translate Chinese text to English for fashion photography descriptions",
        ),
        image_merge,
    ],
    model="gpt-4o"
)

# Main interface function
def merge_model_with_clothing(model_image_path: str,
                               clothing_image_path: str,
                               shot_type: str = "full_body",
                               angle: str = "front",
                               pose_description: str = "natural standing pose",
                               scene_description: str = "minimalist studio background") -> str:
    """
    Merge model with clothing using AI image editing
    
    Args:
        model_image_path: Path to model image
        clothing_image_path: Path to clothing image  
        shot_type: Shot type ("full_body" or "half_body")
        angle: Camera angle ("front" or "side")
        pose_description: Pose description (optional, supports Chinese)
        scene_description: Scene description (optional, supports Chinese)
    
    Returns:
        str: Path to generated image
    """
    print(f"\n🎯 Starting virtual try-on merge...")
    print(f"📸 Model: {model_image_path}")
    print(f"👕 Clothing: {clothing_image_path}")
    print(f"🎬 Settings: {shot_type}, {angle}")
    print(f"💃 Pose: {pose_description}")
    print(f"🏠 Scene: {scene_description}")

    try:
        input_text = f"""
Process virtual try-on task with these parameters:
- Model image path: {model_image_path}
- Clothing image path: {clothing_image_path}
- Shot type: {shot_type}
- Angle: {angle}
- Pose description: {pose_description}
- Scene description: {scene_description}

Please generate a 4-sentence fashion photography prompt. Translate Chinese descriptions to English if needed.
"""

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(Runner.run(agent, input_text))
            final_path = result.final_output
            
            print(f"✅ Virtual try-on completed: {final_path}")
            
        finally:
            loop.close()

        return final_path

    except Exception as e:
        print(f"❌ Virtual try-on failed: {str(e)}")
        raise

__all__ = ["merge_model_with_clothing"]
