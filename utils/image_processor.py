import cv2
import numpy as np
import os
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def process_image(image_path: str) -> str:
    """
    Process image to improve OCR and code detection quality
    Returns path to processed image
    """
    try:
        # Read image using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return image_path
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive threshold to get binary image
        # This helps with text recognition and barcode detection
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply morphological operations to clean up the image
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Denoise the image
        denoised = cv2.fastNlMeansDenoising(cleaned)
        
        # Create processed image path
        base_path, ext = os.path.splitext(image_path)
        processed_path = f"{base_path}_processed{ext}"
        
        # Save processed image
        cv2.imwrite(processed_path, denoised)
        
        logger.info(f"Image processed successfully: {processed_path}")
        return processed_path
        
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return image_path

def enhance_for_ocr(image_path: str) -> str:
    """
    Additional enhancement specifically for OCR
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return image_path
        
        # Resize image if it's too small (OCR works better on larger images)
        height, width = img.shape
        if height < 300 or width < 300:
            scale_factor = max(300 / height, 300 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Apply sharpening filter
        kernel = np.array([[-1, -1, -1],
                          [-1, 9, -1],
                          [-1, -1, -1]])
        sharpened = cv2.filter2D(img, -1, kernel)
        
        # Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharpened)
        
        # Create enhanced image path
        base_path, ext = os.path.splitext(image_path)
        enhanced_path = f"{base_path}_enhanced{ext}"
        
        cv2.imwrite(enhanced_path, enhanced)
        return enhanced_path
        
    except Exception as e:
        logger.error(f"Error enhancing image for OCR {image_path}: {e}")
        return image_path

def preprocess_for_codes(image_path: str) -> str:
    """
    Preprocess image specifically for QR code and barcode detection
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return image_path
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization to improve contrast
        equalized = cv2.equalizeHist(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(equalized, (3, 3), 0)
        
        # Create preprocessed image path
        base_path, ext = os.path.splitext(image_path)
        preprocessed_path = f"{base_path}_codes{ext}"
        
        cv2.imwrite(preprocessed_path, blurred)
        return preprocessed_path
        
    except Exception as e:
        logger.error(f"Error preprocessing image for codes {image_path}: {e}")
        return image_path

def validate_image(image_path: str) -> bool:
    """
    Validate that the file is a readable image
    """
    try:
        # Try to open with PIL first
        with Image.open(image_path) as img:
            img.verify()
        
        # Try to read with OpenCV
        cv_img = cv2.imread(image_path)
        return cv_img is not None
        
    except Exception as e:
        logger.error(f"Image validation failed for {image_path}: {e}")
        return False

def get_image_info(image_path: str) -> dict:
    """
    Get basic information about the image
    """
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height
            }
    except Exception as e:
        logger.error(f"Error getting image info for {image_path}: {e}")
        return {}
