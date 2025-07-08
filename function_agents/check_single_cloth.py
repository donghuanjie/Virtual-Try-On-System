import base64
from openai import OpenAI

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def check_single_cloth(image_path):
    """
    检查图片是否包含单件上衣，适合虚拟试衣
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        bool: True如果图片满足要求，False如果不满足
    """
    try:
        # Getting the Base64 string
        base64_image = encode_image(image_path)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        { 
                            "type": "text", 
                            "text": """
                            Determine whether this image can be used to generate a virtual try-on image with a single top clothing item (such as a shirt, blouse, or jacket). Allow combinations that visually function as one top (e.g., a shirt with an inner layer), as long as they appear as a cohesive unit.

                            Answer with `true` if the clothing in the image can reasonably be treated as one top item for try-on purposes, even if it includes inner layers or accessories. Answer `false` only if the image clearly includes multiple unrelated tops (e.g., jacket + different shirt + cardigan shown distinctly).

                            Return only "true" or "false" without any explanation.
                            """ 
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )

        content = response.choices[0].message.content
        if content is None:
            return False
        result = content.strip().lower()
        return result == "true"
        
    except Exception as e:
        print(f"检查衣服图片时出错: {e}")
        return False


def check_cloth_validity(image_path):
    """
    衣服有效性检查函数，与现有后端API兼容
    
    Args:
        image_path: 图片文件路径
        
    Returns:
        dict: 包含检查结果的字典
    """
    try:
        is_valid = check_single_cloth(image_path)
        
        return {
            "valid": is_valid,
            "error_message": None if is_valid else "图片包含多件上衣或不符合虚拟试衣要求，请上传单件上衣图片"
        }
        
    except Exception as e:
        return {
            "valid": False,
            "error_message": f"图片检查失败: {str(e)}"
        }


# 保留原有的测试功能
if __name__ == "__main__":
    # 测试用的默认路径
    test_image_path = "./uploads/fancy_tshirt.png"
    result = check_single_cloth(test_image_path)
    print(f"检查结果: {result}")
