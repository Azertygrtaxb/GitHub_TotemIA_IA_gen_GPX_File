from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    routes = db.relationship('Route', backref='user', lazy=True)

class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Route preferences
    start_location = db.Column(db.String(100), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # Trail, Hiking, Walking
    experience_level = db.Column(db.String(20), nullable=False)  # Beginner, Intermediate, Expert
    distance_km = db.Column(db.Float, nullable=False)
    landscape_type = db.Column(db.String(50), nullable=False)  # Forest, Mountain, Coastal
    route_type = db.Column(db.String(20), nullable=False)  # Loop, One-way
    elevation_preference = db.Column(db.String(20), nullable=False)  # Flat, Moderate, Difficult
    estimated_duration = db.Column(db.String(20), nullable=False)  # 1h, 2h, 3h+
    ground_type = db.Column(db.String(50))  # Trail, Gravel, Technical
    points_of_interest = db.Column(db.String(100))  # Panoramic view, River, Monument
    
    # Generated route data
    gpx_file_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    total_elevation_gain = db.Column(db.Float)
    actual_distance = db.Column(db.Float)
    coordinates = db.Column(db.Text)  # JSON string of route coordinates
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, generated, sent, failed
    error_message = db.Column(db.Text)
