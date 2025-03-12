from app import db
from datetime import datetime
import json

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    typhoon_name = db.Column(db.String(50))
    typhoon_date = db.Column(db.Date)
    
    # Image paths
    pre_image_path = db.Column(db.String(255))
    post_image_path = db.Column(db.String(255))
    segmented_image_path = db.Column(db.String(255))
    
    # Assessment results
    forest_area_before = db.Column(db.Float)  # Percentage
    forest_area_after = db.Column(db.Float)   # Percentage
    damage_percentage = db.Column(db.Float)   # Percentage
    
    # Additional data (stored as JSON)
    additional_data = db.Column(db.Text)  # JSON string
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def set_additional_data(self, data_dict):
        """Store additional data as JSON string"""
        self.additional_data = json.dumps(data_dict)
    
    def get_additional_data(self):
        """Retrieve additional data from JSON string"""
        if self.additional_data:
            return json.loads(self.additional_data)
        return {}
    
    def __repr__(self):
        return f'<Assessment {self.title}>' 