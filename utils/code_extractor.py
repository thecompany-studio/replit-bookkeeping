import cv2
import numpy as np
from PIL import Image
import os
import logging
import json

# Try to import pyzbar, but handle gracefully if not available
try:
    from pyzbar import pyzbar as _pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    _pyzbar = None
    PYZBAR_AVAILABLE = False

logger = logging.getLogger(__name__)

def extract_codes_from_image(image_path: str) -> list:
    """
    Extract QR codes and barcodes from image using pyzbar
    Returns list of dictionaries with code data
    """
    extracted_codes = []
    
    # Check if pyzbar is available
    if not PYZBAR_AVAILABLE:
        logger.warning("pyzbar library not available - QR/barcode detection disabled")
        return []
    
    try:
        # Validate image exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return extracted_codes
        
        # Try with PIL first
        try:
            with Image.open(image_path) as img:
                if PYZBAR_AVAILABLE and _pyzbar:
                    codes = _pyzbar.decode(img)
                    if codes:
                        for code in codes:
                            code_data = process_decoded_code(code)
                            extracted_codes.append(code_data)
                        logger.info(f"PIL extraction successful: {len(codes)} codes found")
        
        except Exception as pil_error:
            logger.warning(f"PIL code extraction failed, trying OpenCV: {pil_error}")
        
        # If PIL didn't find codes or failed, try with OpenCV preprocessing
        if not extracted_codes:
            try:
                img = cv2.imread(image_path)
                if img is not None:
                    # Convert to grayscale
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    
                    # Try different preprocessing techniques
                    preprocessed_images = [
                        gray,  # Original grayscale
                        cv2.equalizeHist(gray),  # Histogram equalization
                        cv2.GaussianBlur(gray, (3, 3), 0),  # Slight blur
                        cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),  # Adaptive threshold
                    ]
                    
                    for i, processed_img in enumerate(preprocessed_images):
                        try:
                            # Convert back to PIL Image for pyzbar
                            pil_img = Image.fromarray(processed_img)
                            if PYZBAR_AVAILABLE and _pyzbar:
                                codes = _pyzbar.decode(pil_img)
                                
                                if codes:
                                    for code in codes:
                                        code_data = process_decoded_code(code)
                                        # Avoid duplicates
                                        if not any(existing['data'] == code_data['data'] for existing in extracted_codes):
                                            extracted_codes.append(code_data)
                                    
                                    logger.info(f"OpenCV preprocessing {i} successful: {len(codes)} new codes found")
                        
                        except Exception as preprocess_error:
                            logger.debug(f"Preprocessing method {i} failed: {preprocess_error}")
                            continue
            
            except Exception as cv_error:
                logger.warning(f"OpenCV code extraction failed: {cv_error}")
        
        # Try multi-scale detection for small codes
        if not extracted_codes:
            try:
                extracted_codes.extend(multi_scale_detection(image_path))
            except Exception as ms_error:
                logger.warning(f"Multi-scale detection failed: {ms_error}")
        
        logger.info(f"Total codes extracted from {image_path}: {len(extracted_codes)}")
        return extracted_codes
        
    except Exception as e:
        logger.error(f"Error extracting codes from image {image_path}: {e}")
        return extracted_codes

def process_decoded_code(code) -> dict:
    """
    Process a decoded code object from pyzbar into a structured dictionary
    """
    try:
        # Extract code data
        code_data = code.data.decode('utf-8')
        code_type = code.type
        
        # Get bounding box coordinates
        rect = code.rect
        polygon = code.polygon
        
        # Process different types of codes
        processed_data = {
            'type': code_type,
            'data': code_data,
            'raw_data': code.data.hex(),
            'rect': {
                'left': rect.left,
                'top': rect.top,
                'width': rect.width,
                'height': rect.height
            },
            'polygon': [(point.x, point.y) for point in polygon] if polygon else [],
            'extracted_info': extract_code_info(code_data, code_type)
        }
        
        return processed_data
        
    except Exception as e:
        logger.error(f"Error processing decoded code: {e}")
        return {
            'type': str(code.type) if hasattr(code, 'type') else 'unknown',
            'data': 'Error decoding',
            'raw_data': '',
            'rect': {},
            'polygon': [],
            'extracted_info': {}
        }

def extract_code_info(code_data: str, code_type: str) -> dict:
    """
    Extract structured information from code data based on code type
    """
    info = {}
    
    try:
        if code_type == 'QRCODE':
            info = extract_qr_info(code_data)
        elif code_type in ['EAN13', 'EAN8', 'UPCA', 'UPCE']:
            info = extract_barcode_info(code_data, code_type)
        elif code_type == 'CODE128':
            info = extract_code128_info(code_data)
        else:
            # Generic processing for other code types
            info = {
                'content': code_data,
                'length': len(code_data),
                'is_numeric': code_data.isdigit(),
                'is_url': code_data.lower().startswith(('http://', 'https://')),
                'is_email': '@' in code_data and '.' in code_data
            }
    
    except Exception as e:
        logger.error(f"Error extracting info from code data: {e}")
        info = {'error': str(e)}
    
    return info

def extract_qr_info(qr_data: str) -> dict:
    """
    Extract structured information from QR code data
    """
    info = {
        'content': qr_data,
        'length': len(qr_data)
    }
    
    # Check if it's a URL
    if qr_data.lower().startswith(('http://', 'https://')):
        info['type'] = 'url'
        info['url'] = qr_data
    
    # Check if it's a WiFi configuration
    elif qr_data.startswith('WIFI:'):
        info['type'] = 'wifi'
        wifi_parts = qr_data.split(';')
        for part in wifi_parts:
            if ':' in part:
                key, value = part.split(':', 1)
                if key in ['T', 'S', 'P', 'H']:
                    wifi_mapping = {'T': 'security', 'S': 'ssid', 'P': 'password', 'H': 'hidden'}
                    info[wifi_mapping.get(key, key)] = value
    
    # Check if it's contact information (vCard)
    elif qr_data.startswith('BEGIN:VCARD'):
        info['type'] = 'vcard'
        # Parse vCard data
        lines = qr_data.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.lower()] = value
    
    # Check if it's an email
    elif qr_data.startswith('mailto:'):
        info['type'] = 'email'
        info['email'] = qr_data[7:]  # Remove 'mailto:' prefix
    
    # Check if it's a phone number
    elif qr_data.startswith('tel:'):
        info['type'] = 'phone'
        info['phone'] = qr_data[4:]  # Remove 'tel:' prefix
    
    # Check if it's SMS
    elif qr_data.startswith('sms:'):
        info['type'] = 'sms'
        info['phone'] = qr_data[4:]  # Remove 'sms:' prefix
    
    # Check if it's location data
    elif qr_data.startswith('geo:'):
        info['type'] = 'location'
        coords = qr_data[4:].split(',')
        if len(coords) >= 2:
            try:
                info['latitude'] = float(coords[0])
                info['longitude'] = float(coords[1])
            except ValueError:
                pass
    
    # Try to parse as JSON
    else:
        try:
            json_data = json.loads(qr_data)
            info['type'] = 'json'
            info['json_data'] = json_data
        except json.JSONDecodeError:
            info['type'] = 'text'
    
    return info

def extract_barcode_info(barcode_data: str, barcode_type: str) -> dict:
    """
    Extract information from barcode data
    """
    info = {
        'content': barcode_data,
        'barcode_type': barcode_type,
        'length': len(barcode_data)
    }
    
    # For UPC/EAN codes, try to extract product information structure
    if barcode_type in ['EAN13', 'EAN8', 'UPCA', 'UPCE'] and barcode_data.isdigit():
        info['is_product_code'] = True
        
        if barcode_type == 'EAN13' and len(barcode_data) == 13:
            info['country_code'] = barcode_data[:3]
            info['manufacturer_code'] = barcode_data[3:8]
            info['product_code'] = barcode_data[8:12]
            info['check_digit'] = barcode_data[12]
        
        elif barcode_type == 'UPCA' and len(barcode_data) == 12:
            info['manufacturer_code'] = barcode_data[:6]
            info['product_code'] = barcode_data[6:11]
            info['check_digit'] = barcode_data[11]
    
    return info

def extract_code128_info(code_data: str) -> dict:
    """
    Extract information from Code 128 barcode
    """
    info = {
        'content': code_data,
        'length': len(code_data),
        'is_numeric': code_data.isdigit(),
        'is_alphanumeric': code_data.isalnum()
    }
    
    # Code 128 can contain various types of data
    # Check for common patterns
    if code_data.isdigit():
        info['type'] = 'numeric'
    elif any(char.isalpha() for char in code_data):
        info['type'] = 'alphanumeric'
    
    return info

def multi_scale_detection(image_path: str) -> list:
    """
    Try to detect codes at multiple scales for small or hard-to-detect codes
    """
    extracted_codes = []
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            return extracted_codes
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Try different scales
        scales = [0.5, 1.0, 1.5, 2.0]
        
        for scale in scales:
            try:
                # Resize image
                if scale != 1.0:
                    width = int(gray.shape[1] * scale)
                    height = int(gray.shape[0] * scale)
                    resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)
                else:
                    resized = gray
                
                # Convert to PIL for pyzbar
                pil_img = Image.fromarray(resized)
                if PYZBAR_AVAILABLE and _pyzbar:
                    codes = _pyzbar.decode(pil_img)
                else:
                    codes = []
                
                for code in codes:
                    code_data = process_decoded_code(code)
                    # Adjust coordinates back to original scale
                    if scale != 1.0:
                        code_data['rect']['left'] = int(code_data['rect']['left'] / scale)
                        code_data['rect']['top'] = int(code_data['rect']['top'] / scale)
                        code_data['rect']['width'] = int(code_data['rect']['width'] / scale)
                        code_data['rect']['height'] = int(code_data['rect']['height'] / scale)
                        
                        # Adjust polygon coordinates
                        code_data['polygon'] = [(int(x / scale), int(y / scale)) for x, y in code_data['polygon']]
                    
                    # Add scale information
                    code_data['detection_scale'] = scale
                    
                    # Avoid duplicates
                    if not any(existing['data'] == code_data['data'] for existing in extracted_codes):
                        extracted_codes.append(code_data)
            
            except Exception as scale_error:
                logger.debug(f"Multi-scale detection at scale {scale} failed: {scale_error}")
                continue
        
        return extracted_codes
        
    except Exception as e:
        logger.error(f"Error in multi-scale detection: {e}")
        return extracted_codes

def enhance_for_code_detection(image_path: str) -> str:
    """
    Enhance image specifically for better code detection
    """
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return image_path
        
        # Apply different enhancement techniques
        enhanced_images = []
        
        # 1. Histogram equalization
        enhanced_images.append(cv2.equalizeHist(img))
        
        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_images.append(clahe.apply(img))
        
        # 3. Gaussian blur with different kernels
        enhanced_images.append(cv2.GaussianBlur(img, (3, 3), 0))
        enhanced_images.append(cv2.GaussianBlur(img, (5, 5), 0))
        
        # 4. Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        enhanced_images.append(cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel))
        enhanced_images.append(cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel))
        
        # Save the best enhanced version (this is a simplified approach)
        # In practice, you might want to test all versions and return the one with most codes
        base_path, ext = os.path.splitext(image_path)
        enhanced_path = f"{base_path}_enhanced_codes{ext}"
        
        # Use CLAHE enhanced version as it generally works well for codes
        cv2.imwrite(enhanced_path, enhanced_images[1])
        
        return enhanced_path
        
    except Exception as e:
        logger.error(f"Error enhancing image for code detection: {e}")
        return image_path
