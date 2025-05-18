from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeLocalField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError, NumberRange
from datetime import datetime

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=120)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=20, max=2000)])
    location = StringField('Location', validators=[DataRequired(), Length(min=5, max=120)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    start_time = DateTimeLocalField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeLocalField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    category = SelectField('Category', validators=[DataRequired()], choices=[
        ('garage_sale', 'Garage Sale'),
        ('sports', 'Sports Match'),
        ('community_class', 'Community Class'),
        ('volunteer', 'Volunteer Opportunity'),
        ('exhibition', 'Exhibition'),
        ('festival', 'Festival/Celebration')
    ])
    submit = SubmitField('Submit')
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('End time must be after start time.')
    
    def validate_start_time(self, start_time):
        if start_time.data < datetime.now():
            raise ValidationError('Start time cannot be in the past.')

class InterestForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    guests = IntegerField('Number of additional guests', validators=[NumberRange(min=0, max=10)], default=0)
    submit = SubmitField('Express Interest')