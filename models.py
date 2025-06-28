from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import csv
import io

class BookkeepingRecord:
    """In-memory storage model for bookkeeping records"""
    
    def __init__(self, record_id: str, filename: str, upload_date: datetime, 
                 ocr_text: str = "", extracted_codes: List[Dict] = None, 
                 amount: float = 0.0, description: str = "", category: str = "",
                 date: str = "", notes: str = ""):
        self.id = record_id
        self.filename = filename
        self.upload_date = upload_date
        self.ocr_text = ocr_text
        self.extracted_codes = extracted_codes or []
        self.amount = amount
        self.description = description
        self.category = category
        self.date = date
        self.notes = notes
        self.processed_date = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization"""
        return {
            'id': self.id,
            'filename': self.filename,
            'upload_date': self.upload_date.isoformat(),
            'processed_date': self.processed_date.isoformat(),
            'ocr_text': self.ocr_text,
            'extracted_codes': self.extracted_codes,
            'amount': self.amount,
            'description': self.description,
            'category': self.category,
            'date': self.date,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BookkeepingRecord':
        """Create record from dictionary"""
        record = cls(
            record_id=data['id'],
            filename=data['filename'],
            upload_date=datetime.fromisoformat(data['upload_date']),
            ocr_text=data.get('ocr_text', ''),
            extracted_codes=data.get('extracted_codes', []),
            amount=data.get('amount', 0.0),
            description=data.get('description', ''),
            category=data.get('category', ''),
            date=data.get('date', ''),
            notes=data.get('notes', '')
        )
        if 'processed_date' in data:
            record.processed_date = datetime.fromisoformat(data['processed_date'])
        return record

class RecordStorage:
    """In-memory storage for bookkeeping records"""
    
    def __init__(self):
        self.records: Dict[str, BookkeepingRecord] = {}
    
    def add_record(self, record: BookkeepingRecord) -> None:
        """Add a new record to storage"""
        self.records[record.id] = record
    
    def get_record(self, record_id: str) -> Optional[BookkeepingRecord]:
        """Get a record by ID"""
        return self.records.get(record_id)
    
    def get_all_records(self, limit: int = None, offset: int = 0) -> List[BookkeepingRecord]:
        """Get all records with optional pagination"""
        all_records = list(self.records.values())
        # Sort by processed_date descending (newest first)
        all_records.sort(key=lambda x: x.processed_date, reverse=True)
        
        if limit:
            return all_records[offset:offset + limit]
        return all_records[offset:]
    
    def search_records(self, query: str, category: str = "", date_from: str = "", 
                      date_to: str = "") -> List[BookkeepingRecord]:
        """Search records based on various criteria"""
        results = []
        query_lower = query.lower() if query else ""
        
        for record in self.records.values():
            match = True
            
            # Text search in OCR text, description, and notes
            if query_lower:
                text_fields = [
                    record.ocr_text.lower(),
                    record.description.lower(),
                    record.notes.lower(),
                    record.filename.lower()
                ]
                if not any(query_lower in field for field in text_fields):
                    match = False
            
            # Category filter
            if category and record.category != category:
                match = False
            
            # Date range filter
            if date_from and record.date and record.date < date_from:
                match = False
            if date_to and record.date and record.date > date_to:
                match = False
            
            if match:
                results.append(record)
        
        # Sort by processed_date descending
        results.sort(key=lambda x: x.processed_date, reverse=True)
        return results
    
    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for record in self.records.values():
            if record.category:
                categories.add(record.category)
        return sorted(list(categories))
    
    def export_to_json(self) -> str:
        """Export all records to JSON format"""
        records_data = [record.to_dict() for record in self.records.values()]
        return json.dumps(records_data, indent=2, default=str)
    
    def export_to_csv(self) -> str:
        """Export all records to CSV format"""
        output = io.StringIO()
        fieldnames = [
            'id', 'filename', 'upload_date', 'processed_date', 'amount', 
            'description', 'category', 'date', 'notes', 'ocr_text', 'extracted_codes'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in self.records.values():
            row_data = record.to_dict()
            # Convert extracted_codes to string for CSV
            row_data['extracted_codes'] = json.dumps(row_data['extracted_codes'])
            writer.writerow(row_data)
        
        return output.getvalue()
    
    def update_record(self, record_id: str, **kwargs) -> bool:
        """Update an existing record"""
        if record_id not in self.records:
            return False
        
        record = self.records[record_id]
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        return True
    
    def delete_record(self, record_id: str) -> bool:
        """Delete a record"""
        if record_id in self.records:
            del self.records[record_id]
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the records"""
        total_records = len(self.records)
        total_amount = sum(record.amount for record in self.records.values())
        categories = self.get_categories()
        
        # Calculate amounts by category
        category_amounts = {}
        for record in self.records.values():
            if record.category:
                category_amounts[record.category] = category_amounts.get(record.category, 0) + record.amount
        
        return {
            'total_records': total_records,
            'total_amount': total_amount,
            'categories': categories,
            'category_amounts': category_amounts
        }

# Global storage instance
storage = RecordStorage()
