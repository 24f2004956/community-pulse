from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app import db
from models import Event, User
from forms.event_forms import EventForm, InterestForm
from datetime import datetime, timedelta
from services.email_service import send_event_notification
from services.sms_service import send_sms_notification

events_bp = Blueprint('events', __name__)

@events_bp.route('/')
def home():
    # Get upcoming events sorted by start time
    upcoming_events = Event.query.filter(
        Event.start_time > datetime.utcnow(),
        Event.is_approved == True,
        Event.is_cancelled == False
    ).order_by(Event.start_time.asc()).limit(6).all()
    
    return render_template('index.html', events=upcoming_events)

@events_bp.route('/events')
def list_events():
    # Filters
    category = request.args.get('category', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)

    # Base query
    query = Event.query.filter(
        Event.is_approved == True,
        Event.is_cancelled == False,
        Event.start_time > datetime.utcnow()
    )

    # Apply filters
    if category:
        query = query.filter(Event.category == category)
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Event.start_time >= date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Event.start_time <= date_to_obj)
        except ValueError:
            pass

    # Pagination
    pagination = query.order_by(Event.start_time.asc()).paginate(page=page, per_page=6, error_out=False)
    events = pagination.items

    # Categories
    categories = db.session.query(Event.category).distinct().all()
    categories = [cat[0] for cat in categories]

    return render_template(
        'events/list.html',
        events=events,
        pagination=pagination,  # ✅ FIX: now passed to template
        categories=categories,
        selected_category=category,
        date_from=date_from,
        date_to=date_to
    )


@events_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.is_banned:
        flash('You are not allowed to create events.', 'danger')
        return redirect(url_for('events.home'))
    
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            category=form.category.data,
            organizer_id=current_user.id,
            is_approved=current_user.is_verified_organizer  # Auto-approve for verified organizers
        )
        
        db.session.add(event)
        db.session.commit()
        
        if current_user.is_verified_organizer:
            flash('Your event has been created and published!', 'success')
        else:
            flash('Your event has been created and is pending approval.', 'info')
        
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return render_template('events/create.html', form=form, title="Create Event")

@events_bp.route('/events/<int:event_id>')
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if event is cancelled or not approved
    if event.is_cancelled:
        flash('This event has been cancelled.', 'warning')
    elif not event.is_approved and (not current_user.is_authenticated or 
                                    current_user.id != event.organizer_id and 
                                    current_user.role != 'admin'):
        flash('This event is pending approval and is not publicly visible.', 'info')
        return redirect(url_for('events.list_events'))
    
    interest_form = InterestForm()
    
    return render_template(
        'events/detail.html', 
        event=event, 
        interest_form=interest_form,
        title=event.title
    )

@events_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is allowed to edit
    if current_user.id != event.organizer_id and current_user.role != 'admin':
        flash('You are not authorized to edit this event.', 'danger')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    form = EventForm(obj=event)
    
    if form.validate_on_submit():
        # Store old data for notification
        old_start_time = event.start_time
        old_location = event.location
        
        # Update event with form data
        form.populate_obj(event)
        event.updated_at = datetime.utcnow()
        
        # If location or time changed, notify attendees
        should_notify = (old_start_time != event.start_time or old_location != event.location)
        
        db.session.commit()
        
        if should_notify:
            # Notify attendees of changes
            for attendee in event.attendees:
                message = f"Event '{event.title}' has been updated. Please check the details."
                
                # Send email notification
                if attendee.email:
                    send_event_notification(attendee.email, 'update', event, message)
                
                # Send SMS notification if phone is available
                if attendee.phone:
                    send_sms_notification(attendee.phone, message)
        
        flash('Event updated successfully.', 'success')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return render_template('events/edit.html', form=form, event=event, title="Edit Event")

@events_bp.route('/events/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is allowed to cancel
    if current_user.id != event.organizer_id and current_user.role != 'admin':
        flash('You are not authorized to cancel this event.', 'danger')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    event.is_cancelled = True
    db.session.commit()
    
    # Notify attendees
    for attendee in event.attendees:
        message = f"Event '{event.title}' has been cancelled."
        
        # Send email notification
        if attendee.email:
            send_event_notification(attendee.email, 'cancellation', event, message)
        
        # Send SMS notification if phone is available
        if attendee.phone:
            send_sms_notification(attendee.phone, message)
    
    flash('Event has been cancelled.', 'info')
    return redirect(url_for('events.view_event', event_id=event.id))

@events_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Check if user is allowed to delete
    if current_user.id != event.organizer_id and current_user.role != 'admin':
        flash('You are not authorized to delete this event.', 'danger')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Event has been deleted.', 'success')
    return redirect(url_for('events.list_events'))

@events_bp.route('/events/<int:event_id>/interest', methods=['POST'])
def express_interest(event_id):
    event = Event.query.get_or_404(event_id)
    
    if event.is_cancelled:
        flash('This event has been cancelled.', 'warning')
        return redirect(url_for('events.view_event', event_id=event.id))
    
    form = InterestForm()
    if form.validate_on_submit():
        # Handle guest attendee
        if not current_user.is_authenticated:
            # Check if email already exists
            user = User.query.filter_by(email=form.email.data).first()
            
            if not user:
                # Create a temporary user
                user = User(
                    username=form.email.data.split('@')[0],  # Use email prefix as username
                    email=form.email.data,
                    phone=form.phone.data
                )
                user.set_password('temporary')  # Set a placeholder password
                db.session.add(user)
                db.session.commit()
            
            # Add user as attendee with guest count
            event.attendees.append(user)
            db.session.commit()
            
            flash('Your interest has been registered!', 'success')
        else:
            # Logged in user
            user = current_user
            
            # Check if already attending
            if user in event.attendees:
                flash('You are already registered for this event.', 'info')
            else:
                event.attendees.append(user)
                db.session.commit()
                flash('Your interest has been registered!', 'success')
        
        # Schedule reminder notification
        reminder_time = event.start_time - timedelta(days=1)
        if reminder_time > datetime.utcnow():
            message = f"Reminder: The event '{event.title}' is tomorrow!"
            
            # TODO: Schedule email notification
            # TODO: Schedule SMS notification if phone is available
        
        return redirect(url_for('events.view_event', event_id=event.id))
    
    return redirect(url_for('events.view_event', event_id=event.id))

@events_bp.route('/api/events/nearby')
def nearby_events():
    # Get user location
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    if not lat or not lng:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    # Get events within a radius (approximately 10km)
    # This is a simple approximation, in production you would use a proper geospatial query
    radius = 0.1  # Approximately 10km in latitude/longitude
    
    nearby_events = Event.query.filter(
        Event.latitude.between(lat - radius, lat + radius),
        Event.longitude.between(lng - radius, lng + radius),
        Event.start_time > datetime.utcnow(),
        Event.is_approved == True,
        Event.is_cancelled == False
    ).all()
    
    return jsonify({
        'events': [event.to_dict() for event in nearby_events]
    })