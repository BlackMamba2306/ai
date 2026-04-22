import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image

# Load the model once when the server starts
model = MobileNetV2(weights='imagenet')

def analyze_image(img_path):
    # 1. Load and resize image to 224x224 (required by MobileNetV2)
    img = image.load_img(img_path, target_size=(224, 224))
    
    # 2. Convert to array and preprocess
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = preprocess_input(img_array)

    # 3. Predict
    predictions = model.predict(img_array)
    
    # 4. Decode results (get the top 3 possibilities)
    results = decode_predictions(predictions, top=3)[0]
    
    # Return the name of the most likely object
    return results[0][1] # Example: 'sneaker' or 't-shirt'