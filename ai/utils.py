from PIL import Image
import torch
from torchvision import transforms


# basic ResNet50 preprocessing – your teammate can adjust if needed
_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def load_image(path):
    """
    path: pathlib.Path or string path to saved image
    returns: tensor of shape (1, 3, 224, 224)
    """
    img = Image.open(path).convert("RGB")
    tensor = _transform(img).unsqueeze(0)
    return tensor
