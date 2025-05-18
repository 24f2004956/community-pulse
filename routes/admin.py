from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from models import User, Event
from extensions import db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin-required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash("You are not authorized to access this page.", "danger")
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_events = Event.query.count()
    pending_events = Event.query.filter_by(is_approved=False, is_cancelled=False).count()
    approved_events = Event.query.filter_by(is_approved=True, is_cancelled=False).count()
    
    recent_pending = Event.query.filter_by(is_approved=False, is_cancelled=False)\
                                .order_by(Event.created_at.desc()).limit(5).all()
    
    return render_template(
        'admin/dashboard.html',
        title='Admin Dashboard',
        total_users=total_users,
        total_events=total_events,
        pending_events=pending_events,
        approved_events=approved_events,
        recent_pending=recent_pending
    )

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', title='User Management', users=users)

@admin_bp.route('/users/<int:user_id>/toggle_ban', methods=['POST'])
@login_required
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        flash('You cannot ban another admin.', 'danger')
        return redirect(url_for('admin.user_list'))

    user.is_banned = not user.is_banned
    db.session.commit()
    
    action = 'banned' if user.is_banned else 'unbanned'
    flash(f'User {user.username} has been {action}.', 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/users/<int:user_id>/toggle_organizer', methods=['POST'])
@login_required
@admin_required
def toggle_organizer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_verified_organizer = not user.is_verified_organizer
    db.session.commit()
    
    status = "granted" if user.is_verified_organizer else "revoked"
    flash(f'Organizer status {status} for {user.username}.', 'success')
    return redirect(url_for('admin.user_list'))

@admin_bp.route('/events')
@login_required
@admin_required
def event_list():
    status = request.args.get('status', 'pending')
    
    if status == 'pending':
        events = Event.query.filter_by(is_approved=False, is_cancelled=False)\
                            .order_by(Event.created_at.desc()).all()
    elif status == 'approved':
        events = Event.query.filter_by(is_approved=True, is_cancelled=False)\
                            .order_by(Event.start_time.desc()).all()
    elif status == 'cancelled':
        events = Event.query.filter_by(is_cancelled=True)\
                            .order_by(Event.updated_at.desc()).all()
    else:
        events = Event.query.order_by(Event.created_at.desc()).all()
    
    return render_template('admin/events.html', title='Event Management', events=events, status=status)

@admin_bp.route('/events/<int:event_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.is_approved = True
    db.session.commit()
    
    flash(f'Event "{event.title}" approved.', 'success')
    return redirect(url_for('admin.event_list', status='pending'))

@admin_bp.route('/events/<int:event_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.is_cancelled = True
    db.session.commit()
    
    flash(f'Event "{event.title}" rejected.', 'warning')
    return redirect(url_for('admin.event_list', status='pending'))

@admin_bp.route('/events/<int:event_id>/view')
@login_required
@admin_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('admin/event_detail.html', title='Event Details', event=event)

@admin_bp.route('/events/<int:event_id>/flag', methods=['POST'])
@login_required
@admin_required
def flag_event(event_id):
    event = Event.query.get_or_404(event_id)
    reason = request.form.get('reason', '')
    # Implement actual flagging logic here (e.g., log, flag table, etc.)
    
    flash(f'Event "{event.title}" flagged for: {reason}', 'warning')
    return redirect(url_for('admin.event_list'))
