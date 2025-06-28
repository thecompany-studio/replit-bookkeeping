import os
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.utils import secure_filename
from app import app
from models import BookkeepingRecord, storage
from utils.image_processor import process_image
from utils.ocr_processor import extract_text_from_image
from utils.code_extractor_simple import extract_codes_from_image
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    """Decorator to require admin login"""
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Home page - redirect to login if not authenticated, otherwise dashboard"""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        secret = request.form.get('secret', '').strip()
        
        if secret == app.config['ADMIN_SECRET']:
            session['admin_logged_in'] = True
            session['login_time'] = datetime.now().isoformat()
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid admin secret. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing overview and recent records"""
    stats = storage.get_stats()
    recent_records = storage.get_all_records(limit=5)
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_records=recent_records)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload and process images"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Generate unique filename
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save uploaded file
                file.save(filepath)
                logger.info(f"File saved: {filepath}")
                
                # Process the image
                processed_image_path = process_image(filepath)
                
                # Extract OCR text
                ocr_text = extract_text_from_image(processed_image_path)
                logger.info(f"OCR text extracted: {len(ocr_text)} characters")
                
                # Extract QR codes and barcodes
                extracted_codes = extract_codes_from_image(processed_image_path)
                logger.info(f"Codes extracted: {len(extracted_codes)} codes")
                
                # Create record
                record_id = str(uuid.uuid4())
                record = BookkeepingRecord(
                    record_id=record_id,
                    filename=filename,
                    upload_date=datetime.now(),
                    ocr_text=ocr_text,
                    extracted_codes=extracted_codes
                )
                
                # Store record
                storage.add_record(record)
                
                # Clean up temporary files
                try:
                    os.remove(filepath)
                    if processed_image_path != filepath:
                        os.remove(processed_image_path)
                except OSError as e:
                    logger.warning(f"Could not remove temporary file: {e}")
                
                flash(f'Image processed successfully! OCR extracted {len(ocr_text)} characters, found {len(extracted_codes)} codes.', 'success')
                return redirect(url_for('edit_record', record_id=record_id))
                
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                flash(f'Error processing image: {str(e)}', 'danger')
        else:
            flash('Invalid file type. Please upload an image file.', 'danger')
    
    return render_template('upload.html')

@app.route('/records')
@login_required
def records():
    """View all records with search and filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    
    # Get records based on search criteria
    if query or category or date_from or date_to:
        all_records = storage.search_records(query, category, date_from, date_to)
    else:
        all_records = storage.get_all_records()
    
    # Pagination
    total_records = len(all_records)
    offset = (page - 1) * per_page
    records_page = all_records[offset:offset + per_page]
    
    # Calculate pagination info
    total_pages = (total_records + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    categories = storage.get_categories()
    
    return render_template('records.html',
                         records=records_page,
                         categories=categories,
                         query=query,
                         category=category,
                         date_from=date_from,
                         date_to=date_to,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         total_records=total_records)

@app.route('/record/<record_id>')
@login_required
def view_record(record_id):
    """View individual record details"""
    record = storage.get_record(record_id)
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records'))
    
    return render_template('record_detail.html', record=record)

@app.route('/record/<record_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_record(record_id):
    """Edit record details"""
    record = storage.get_record(record_id)
    if not record:
        flash('Record not found.', 'danger')
        return redirect(url_for('records'))
    
    if request.method == 'POST':
        try:
            # Update record with form data
            amount = float(request.form.get('amount', 0))
            updates = {
                'amount': amount,
                'description': request.form.get('description', '').strip(),
                'category': request.form.get('category', '').strip(),
                'date': request.form.get('date', '').strip(),
                'notes': request.form.get('notes', '').strip()
            }
            
            storage.update_record(record_id, **updates)
            flash('Record updated successfully!', 'success')
            return redirect(url_for('view_record', record_id=record_id))
            
        except ValueError:
            flash('Invalid amount value.', 'danger')
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            flash(f'Error updating record: {str(e)}', 'danger')
    
    categories = storage.get_categories()
    return render_template('edit_record.html', record=record, categories=categories)

@app.route('/record/<record_id>/delete', methods=['POST'])
@login_required
def delete_record(record_id):
    """Delete a record"""
    if storage.delete_record(record_id):
        flash('Record deleted successfully.', 'success')
    else:
        flash('Record not found.', 'danger')
    
    return redirect(url_for('records'))

@app.route('/export/<format>')
@login_required
def export_records(format):
    """Export records in JSON or CSV format"""
    if format not in ['json', 'csv']:
        flash('Invalid export format.', 'danger')
        return redirect(url_for('records'))
    
    try:
        if format == 'json':
            data = storage.export_to_json()
            response = make_response(data)
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = f'attachment; filename=bookkeeping_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        else:  # CSV
            data = storage.export_to_csv()
            response = make_response(data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=bookkeeping_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting records: {e}")
        flash(f'Error exporting records: {str(e)}', 'danger')
        return redirect(url_for('records'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File is too large. Maximum size is 16MB.', 'danger')
    return redirect(url_for('upload'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return render_template('500.html'), 500
