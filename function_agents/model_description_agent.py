import json
from typing import Dict, Optional, List, Union
from pydantic import BaseModel, Field
from agents import Agent, Runner
import asyncio
from string import Template

TEMPLATE = Template("""
Model Specifications:
Gender: $gender
Age: $age
Nationality: $nationality
Height: $height cm
Weight: $weight kg
""")

class ModelDescription(BaseModel):
    """Model description data structure focusing on basic model characteristics"""
    prompt: str = Field(..., description="Main prompt text for GPT-image-1")

class ModelDescriptionAgent:
    def __init__(self):
        """Initialize GPT-4o based model description generator"""
        self.agent = Agent(
            name="Model Description Generator",
            instructions="""
You are a professional prompt engineer for GPT-image-1 fashion model generation, specializing in virtual try-on applications.

Based on the user's provided attributes — gender, age, ethnicity, height, and weight — generate a **natural English sentence** that describes a professional studio model with clean body detail and no distractions.

**Purpose**: The resulting image will be used as a base for virtual clothing try-on, so the model must be clearly visible with full-body detail, wearing neutral base clothing.

INCLUDE:
- Model's appearance: age, gender, ethnicity, approximate body build inferred from height and weight
- Standing in a natural, upright posture with confident demeanor
- Facial and body details should be clear and realistic
- Clothing: plain, fitted white or light gray t-shirt and basic jeans or pants with no patterns or logos
- Studio-quality lighting with a clean, pure background (preferably white or light gray)

EXCLUDE:
- Any props, lighting equipment, logos, background objects, or on-image text
- Any dramatic camera angles or cropped views
- Any accessories like hats, glasses, jewelry, or makeup

Return one natural, fluent English sentence that describes the model and setting. Output should only include the `prompt` field — do not add any explanations or formatting.

Example output:
"A confident 26-year-old Black female model, 165cm tall and 58kg with a curvy but fit build, wearing a plain light gray fitted t-shirt and basic black jeans, standing naturally in a professional white studio with no props."
"""
,
            output_type=ModelDescription,
            model="gpt-4o"
        )
    
    def generate_description(self, model_specs: Dict) -> str:
        """
        Generate model description using GPT-4o, fallback to template if failed
        
        Args:
            model_specs: Model specification dictionary containing gender, age, nationality, height, weight
            
        Returns:
            Optimized model description text (basic model characteristics only)
        """
        try:
            # Build input prompt
            input_prompt = self._build_input_prompt(model_specs)
            
            # Try to use async in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(Runner.run(self.agent, input_prompt))
                description_data = result.final_output_as(ModelDescription)
                return description_data.prompt
            finally:
                loop.close()
                
        except Exception as e:
            print(f"⚠️ GPT-4o generation failed, using fallback template: {e}")
            return self._fallback_generation(model_specs)
    
    def _build_input_prompt(self, model_specs: Dict) -> str:
        # Build template parameters - only basic model information
        template_params = {
            'gender': model_specs.get('gender', 'female'),
            'age': model_specs.get('age', 25),
            'nationality': model_specs.get('nationality', 'Chinese'),
            'height': model_specs.get('height', 170),
            'weight': model_specs.get('weight', 60)
        }
        
        return TEMPLATE.substitute(template_params)
    
    def _fallback_generation(self, model_specs: Dict) -> str:
        """Fallback generation method for basic model description with simple base clothing"""
        gender = model_specs.get('gender', 'female')
        age = model_specs.get('age', 25)
        nationality = model_specs.get('nationality', 'Chinese')
        height = model_specs.get('height', 170)
        weight = model_specs.get('weight', 60)
        
        # Determine body type based on BMI
        bmi = weight / ((height / 100) ** 2)
        if bmi < 18.5:
            body_type = "slim and elegant"
        elif bmi < 24:
            body_type = "fit and well-proportioned"
        elif bmi < 28:
            body_type = "curvy and attractive"
        else:
            body_type = "plus-size and confident"
        
        # Choose appropriate base clothing based on gender
        if gender.lower() in ['female', 'woman']:
            base_clothing = "wearing a simple white fitted t-shirt and basic blue jeans"
        else:
            base_clothing = "wearing a simple white t-shirt and basic dark jeans"
        
        # Generate basic model description with appropriate base clothing
        description = f"A confident {age}-year-old {nationality} {gender} model, {height}cm tall with a {body_type} build, {base_clothing}, standing naturally with excellent posture, professional studio lighting, clean neutral background."
        
        return description

# Simple factory function
def create_model_description_agent() -> ModelDescriptionAgent:
    """Create model description generator instance"""
    return ModelDescriptionAgent()

# Simple interface
def generate_model_description(model_specs: Dict) -> str:
    """
    Generate model description - simple interface (basic model characteristics only)
    
    Args:
        model_specs: Model specification parameters (gender, age, nationality, height, weight)
        
    Returns:
        Generated model description text (basic model characteristics only)
    """
    agent = create_model_description_agent()
    return agent.generate_description(model_specs)