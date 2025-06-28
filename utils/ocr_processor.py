import pytesseract
import cv2
from PIL import Image
import os
import logging
import re

logger = logging.getLogger(__name__)

# Configure Tesseract path if needed (uncomment and adjust for your system)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image using Tesseract OCR
    """
    try:
        # Validate image exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return ""
        
        # First, try with PIL
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Use Tesseract with custom configuration for better results
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{}|;:,.<>?/~` '
                text = pytesseract.image_to_string(img, config=custom_config)
                
                if text.strip():
                    logger.info(f"OCR extraction successful using PIL: {len(text)} characters")
                    return clean_ocr_text(text)
        
        except Exception as pil_error:
            logger.warning(f"PIL OCR failed, trying OpenCV: {pil_error}")
        
        # If PIL fails, try with OpenCV
        try:
            img = cv2.imread(image_path)
            if img is not None:
                # Convert BGR to RGB
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                text = pytesseract.image_to_string(img_rgb)
                
                if text.strip():
                    logger.info(f"OCR extraction successful using OpenCV: {len(text)} characters")
                    return clean_ocr_text(text)
        
        except Exception as cv_error:
            logger.warning(f"OpenCV OCR failed: {cv_error}")
        
        # Try with different PSM modes if the above fails
        psm_modes = [6, 8, 13, 11, 12]  # Different page segmentation modes
        
        for psm in psm_modes:
            try:
                custom_config = f'--oem 3 --psm {psm}'
                text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)
                
                if text.strip():
                    logger.info(f"OCR extraction successful with PSM {psm}: {len(text)} characters")
                    return clean_ocr_text(text)
            
            except Exception as psm_error:
                logger.debug(f"PSM {psm} failed: {psm_error}")
                continue
        
        logger.warning(f"No text could be extracted from image: {image_path}")
        return ""
        
    except Exception as e:
        logger.error(f"Error extracting text from image {image_path}: {e}")
        return ""

def clean_ocr_text(text: str) -> str:
    """
    Clean and normalize OCR text output
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common OCR artifacts
    text = re.sub(r'[^\w\s\-.,!@#$%^&*()_+=\[\]{}|;:,.<>?/~`"]', '', text)
    
    # Fix common OCR mistakes
    replacements = {
        '0': ['O', 'o'],  # Numbers often confused with letters
        '1': ['l', 'I'],
        '5': ['S'],
        '6': ['G'],
        '8': ['B'],
    }
    
    # Apply replacements in context (for numbers that should be letters)
    # This is a simple heuristic - in a production system, you might use ML models
    
    return text.strip()

def extract_structured_data(ocr_text: str) -> dict:
    """
    Extract structured data from OCR text (amounts, dates, etc.)
    """
    structured_data = {
        'amounts': [],
        'dates': [],
        'emails': [],
        'phone_numbers': [],
        'invoice_numbers': []
    }
    
    if not ocr_text:
        return structured_data
    
    # Extract monetary amounts
    amount_patterns = [
        r'\$\s*\d+\.?\d*',  # $123.45
        r'\d+\.\d{2}\s*USD',  # 123.45 USD
        r'USD\s*\d+\.?\d*',  # USD 123.45
        r'\d{1,3}(?:,\d{3})*\.?\d*',  # 1,234.56
    ]
    
    for pattern in amount_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        structured_data['amounts'].extend(matches)
    
    # Extract dates
    date_patterns = [
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # MM/DD/YYYY or MM-DD-YYYY
        r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{2,4}\b',  # DD MMM YYYY
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        structured_data['dates'].extend(matches)
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    structured_data['emails'] = re.findall(email_pattern, ocr_text)
    
    # Extract phone numbers
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # XXX-XXX-XXXX
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',  # (XXX) XXX-XXXX
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, ocr_text)
        structured_data['phone_numbers'].extend(matches)
    
    # Extract potential invoice numbers
    invoice_patterns = [
        r'(?:Invoice|INV|Receipt|RCP)[\s#:]*([A-Z0-9-]+)',
        r'#\s*([A-Z0-9-]{3,})',
    ]
    
    for pattern in invoice_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        structured_data['invoice_numbers'].extend(matches)
    
    # Remove duplicates
    for key in structured_data:
        structured_data[key] = list(set(structured_data[key]))
    
    return structured_data

def get_ocr_confidence(image_path: str) -> float:
    """
    Get OCR confidence score for the extracted text
    """
    try:
        with Image.open(image_path) as img:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Calculate average confidence (excluding -1 values)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            
            if confidences:
                return sum(confidences) / len(confidences)
            else:
                return 0.0
                
    except Exception as e:
        logger.error(f"Error getting OCR confidence for {image_path}: {e}")
        return 0.0

def extract_text_with_coordinates(image_path: str) -> list:
    """
    Extract text with bounding box coordinates
    """
    try:
        with Image.open(image_path) as img:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            text_elements = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:  # Only include text with reasonable confidence
                    text_elements.append({
                        'text': data['text'][i],
                        'left': data['left'][i],
                        'top': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            
            return text_elements
            
    except Exception as e:
        logger.error(f"Error extracting text with coordinates from {image_path}: {e}")
        return []
