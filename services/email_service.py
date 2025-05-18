from flask_mail import Message, Mail
from flask import current_app
from app import db
from models import Notification
import os

# Initialize Flask-Mail
mail = Mail()

def send_event_notification(email, notification_type, event, message):
    """
    Send email notification about an event
    
    Args:
        email (str): Recipient email address
        notification_type (str): Type of notification ('reminder', 'update', 'cancellation')
        event (Event): Event object
        message (str): Notification message
    """
    try:
        with current_app.app_context():
            subject = ""
            if notification_type == 'reminder':
                subject = f"Reminder: {event.title} is tomorrow!"
            elif notification_type == 'update':
                subject = f"Update: Changes to {event.title}"
            elif notification_type == 'cancellation':
                subject = f"Cancellation: {event.title}"
            else:
                subject = f"Community Pulse: {event.title}"
            
            msg = Message(
                subject=subject,
                recipients=[email],
                body=f"""
                {message}
                
                Event Details:
                - Title: {event.title}
                - Date: {event.start_time.strftime('%A, %B %d, %Y')}
                - Time: {event.start_time.strftime('%I:%M %p')} - {event.end_time.strftime('%I:%M %p')}
                - Location: {event.location}
                
                You can view full details at: http://localhost:5000/events/{event.id}
                
                Community Pulse
                """
            )
            
            mail.send(msg)
            
            # Record the notification
            notification = Notification(
                user_id=event.id,  # This is a placeholder, ideally you'd have the user ID
                event_id=event.id,
                type=notification_type,
                message=message,
                is_sent=True
            )
            
            db.session.add(notification)
            db.session.commit()
            
            return True
    except Exception as e:
        print(f"Error sending email notification: {str(e)}")
        return False

def send_batch_reminders():
    """
    Send reminders for events happening tomorrow
    This would be called by a scheduled task
    """
    # Implementation would go here
    pass