import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# ==== SETUP ====
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Load model once
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32", use_safetensors=True).to(DEVICE)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)


# ==== DETECTION FUNCTION ====
def is_sneaker(image_path, threshold=0.741):
    """
    Detect if an image contains a sneaker.
    
    Args:
        image_path: Path to image file
        threshold: Classification threshold (default: 0.741) ma t8ayeraassh!!!
    
    Returns:
        dict: {
            'is_sneaker': bool,
            'probability': float,
            'confidence': str
        }
    """
    img = Image.open(image_path).convert("RGB")
    
    texts = [
        "a photo of a sneaker",
        "a photo of athletic shoes", 
        "a photo of running shoes",
        "a photo of sports footwear",
        "not a shoe",
        "random object",
        "a photo of clothing",
        "a photo of a vehicle",
        "a photo of an animal",
        "a photo of food"
    ]
    
    inputs = processor(text=texts, images=img, return_tensors="pt", padding=True).to(DEVICE)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = outputs.logits_per_image.softmax(dim=1)
    
    shoe_prob = float(probs[0][:4].sum())
    is_sneaker_result = shoe_prob >= threshold
    
    if is_sneaker_result:
        confidence = "high" if shoe_prob >= 0.85 else "medium"
    else:
        confidence = "high" if shoe_prob <= 0.30 else "medium"
    
    return {
        "is_sneaker": is_sneaker_result,
        "probability": round(shoe_prob, 3),
        "confidence": confidence
    }


# ==== USAGE ====
if __name__ == "__main__":
    # Example usage
    result = is_sneaker("testing images/jordan1.jpeg")
    print(result)
    # Output: {'is_sneaker': True, 'probability': 0.905, 'confidence': 'high'}