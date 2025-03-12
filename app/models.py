from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import logging

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    assessments = db.relationship('Assessment', backref='author', lazy=True)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Add UserMixin methods
    def is_authenticated(self):
        return True
        
    def is_active(self):
        return True
        
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return str(self.id)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    typhoon_name = db.Column(db.String(50), nullable=True)
    typhoon_date = db.Column(db.Date, nullable=True)
    pre_image_path = db.Column(db.String(255), nullable=True)
    post_image_path = db.Column(db.String(255), nullable=True)
    segmented_image_path = db.Column(db.String(255), nullable=True)
    forest_area_before = db.Column(db.Float, nullable=True)
    forest_area_after = db.Column(db.Float, nullable=True)
    damage_percentage = db.Column(db.Float, nullable=True)
    additional_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"Assessment('{self.title}', '{self.location}', '{self.created_at}')"
    
    # Property aliases to maintain compatibility with existing code
    @property
    def name(self):
        return self.title
        
    @name.setter
    def name(self, value):
        self.title = value
    
    @property
    def date(self):
        return self.created_at
        
    @date.setter
    def date(self, value):
        self.created_at = value
    
    @property
    def pre_image(self):
        return self.pre_image_path
        
    @pre_image.setter
    def pre_image(self, value):
        self.pre_image_path = value
    
    @property
    def post_image(self):
        return self.post_image_path
        
    @post_image.setter
    def post_image(self, value):
        self.post_image_path = value
    
    # Add processed field as a property
    @property
    def processed(self):
        return self.damage_percentage is not None
    
    @processed.setter
    def processed(self, value):
        # This is a computed property based on damage_percentage
        # If value is True and damage_percentage is None, set a default value
        # If value is False, we could set damage_percentage to None, but that would lose data
        # So we'll just log a warning and not change anything
        if value and self.damage_percentage is None:
            logging.warning("Setting processed=True but damage_percentage is None. This shouldn't happen.")
            # We don't actually need to do anything here since processed is computed from damage_percentage
        elif not value and self.damage_percentage is not None:
            logging.warning("Setting processed=False but damage_percentage exists. This would lose data.")
            # We don't actually need to do anything here since processed is computed from damage_percentage
    
    @property
    def processed_date(self):
        return self.updated_at
        
    @processed_date.setter
    def processed_date(self, value):
        self.updated_at = value
    
    # Add visualization paths as properties
    @property
    def pre_vis_path(self):
        return self.segmented_image_path
        
    @pre_vis_path.setter
    def pre_vis_path(self, value):
        self.segmented_image_path = value
    
    # Store these in additional_data as JSON
    @property
    def post_vis_path(self):
        import json
        if self.additional_data and 'post_vis_path' in json.loads(self.additional_data or '{}'):
            return json.loads(self.additional_data)['post_vis_path']
        return None
        
    @post_vis_path.setter
    def post_vis_path(self, value):
        import json
        data = json.loads(self.additional_data or '{}')
        data['post_vis_path'] = value
        self.additional_data = json.dumps(data)
    
    @property
    def change_vis_path(self):
        import json
        if self.additional_data and 'change_vis_path' in json.loads(self.additional_data or '{}'):
            return json.loads(self.additional_data)['change_vis_path']
        return None
        
    @change_vis_path.setter
    def change_vis_path(self, value):
        import json
        data = json.loads(self.additional_data or '{}')
        data['change_vis_path'] = value
        self.additional_data = json.dumps(data) 