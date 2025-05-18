from datetime import datetime
from extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for attendees
event_attendee = db.Table('event_attendee',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
    db.Column('num_guests', db.Integer, default=0),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    is_verified_organizer = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    
    # Relationships
    created_events = db.relationship('Event', backref='organizer', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_approved = db.Column(db.Boolean, default=False)
    is_cancelled = db.Column(db.Boolean, default=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    attendees = db.relationship('User', 
                               secondary=event_attendee,
                               backref=db.backref('attending_events', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Event {self.title}>'
    
    def to_dict(self):
        """Convert event to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'category': self.category,
            'is_approved': self.is_approved,
            'is_cancelled': self.is_cancelled,
            'organizer_id': self.organizer_id,
            'organizer_name': self.organizer.username
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'reminder', 'update', 'cancellation'
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_sent = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='notifications')
    event = db.relationship('Event', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id} for {self.user.username}>'


# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

