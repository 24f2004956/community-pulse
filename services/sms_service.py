from flask import current_app
from twilio.rest import Client
import os

def send_sms_notification(phone_number, message):
    """
    Send SMS notification using Twilio
    
    Args:
        phone_number (str): Recipient phone number
        message (str): Message to send
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        auth_token = current_app.config['TWILIO_AUTH_TOKEN']
        from_number = current_app.config['TWILIO_PHONE_NUMBER']
        
        # Skip if Twilio is not configured
        if not account_sid or not auth_token or not from_number:
            print("Twilio not configured, skipping SMS notification")
            return False
        
        client = Client(account_sid, auth_token)
        
        # Send SMS
        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=phone_number
        )
        
        print(f"SMS sent: {sms.sid}")
        return True
    except Exception as e:
        print(f"Error sending SMS notification: {str(e)}")
        return False