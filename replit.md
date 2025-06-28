# Bookkeeping App

## Overview

This is a Flask-based bookkeeping application designed to process receipt and invoice images through OCR (Optical Character Recognition) and barcode/QR code detection. The app provides a simple admin interface for uploading images, extracting financial data, and managing bookkeeping records.

## System Architecture

The application follows a traditional Flask web application architecture with the following layers:

- **Presentation Layer**: HTML templates with Bootstrap UI framework
- **Application Layer**: Flask routes handling HTTP requests and responses  
- **Business Logic Layer**: Utility modules for image processing, OCR, and code extraction
- **Data Layer**: In-memory storage using Python data structures (no persistent database)

The architecture is designed for simplicity and ease of deployment, prioritizing functionality over scalability for small-scale bookkeeping needs.

## Key Components

### Backend Components

1. **Flask Application** (`app.py`, `main.py`)
   - Main Flask app configuration with session management
   - File upload handling with size limits (16MB)
   - Admin authentication using environment-based secrets
   - ProxyFix middleware for proper request handling

2. **Routes** (`routes.py`)
   - Admin login system with session-based authentication
   - Dashboard with statistics and recent records
   - File upload endpoint with validation
   - Records management with search and filtering
   - Export functionality for CSV downloads

3. **Data Models** (`models.py`)
   - In-memory BookkeepingRecord model
   - JSON serialization/deserialization support
   - Built-in storage management functions

4. **Image Processing Utilities** (`utils/`)
   - **OCR Processor**: Tesseract-based text extraction with multiple fallback strategies
   - **Code Extractor**: QR code and barcode detection using pyzbar and OpenCV
   - **Image Processor**: Image preprocessing for improved OCR accuracy

### Frontend Components

1. **Templates** (`templates/`)
   - Bootstrap-based responsive design with dark theme
   - Base template with navigation and common elements
   - Specialized pages for login, dashboard, upload, and records

2. **Static Assets** (`static/`)
   - Custom CSS for enhanced styling
   - JavaScript for interactive features and form validation

## Data Flow

1. **Authentication**: Admin enters secret key to access the application
2. **Upload Process**: 
   - User uploads image file through web interface
   - File validation and secure storage in uploads directory
   - Image preprocessing using OpenCV filters
   - OCR text extraction using Tesseract
   - QR/barcode detection using pyzbar
3. **Data Management**: Records stored in memory with manual editing capabilities
4. **Export**: Records can be exported as CSV files for external use

## External Dependencies

### Python Libraries
- **Flask**: Web framework and session management
- **OpenCV**: Image preprocessing and computer vision
- **Tesseract/pytesseract**: OCR text extraction
- **pyzbar**: QR code and barcode detection
- **Pillow (PIL)**: Image handling and format conversion
- **Werkzeug**: WSGI utilities and security

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Custom Bootstrap theme**: Replit-optimized dark theme

### System Requirements
- Tesseract OCR engine must be installed on the system
- OpenCV dependencies for image processing
- Write permissions for uploads directory

## Deployment Strategy

The application is designed for simple deployment scenarios:

1. **Development**: Direct Flask development server (configured in main.py)
2. **Production**: WSGI-compatible server (Gunicorn, uWSGI) with ProxyFix middleware
3. **Environment Variables**:
   - `SESSION_SECRET`: Flask session encryption key
   - `ADMIN_SECRET`: Admin authentication password
4. **File Storage**: Local filesystem with configurable upload directory
5. **No Database**: All data stored in memory (resets on restart)

### Deployment Considerations
- Uploads directory must be writable
- Tesseract OCR must be installed and accessible
- 16MB file upload limit configured
- Session data stored on filesystem

## Changelog

```
Changelog:
- June 28, 2025. Initial setup
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```

## Technical Notes

- **No Persistent Storage**: The application uses in-memory storage, meaning all records are lost when the application restarts. This design choice prioritizes simplicity over data persistence.
- **Admin Authentication**: Simple secret-based authentication suitable for single-user scenarios.
- **Image Processing Pipeline**: Multi-stage processing with fallback strategies to maximize OCR and code detection success rates.
- **Responsive Design**: Bootstrap-based UI that works on desktop and mobile devices.
- **Error Handling**: Comprehensive logging and graceful degradation when processing fails.

The application is ideal for small businesses or individuals who need basic receipt processing capabilities without the complexity of a full-featured accounting system.