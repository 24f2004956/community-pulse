from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Issue, db
from flask_login import login_required, current_user

issues_bp = Blueprint('issues', __name__, url_prefix='/issues')

@issues_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        location_text = request.form.get('location')
        is_anonymous = request.form.get('is_anonymous') == 'on'

        issue = Issue(
            title=title,
            description=description,
            category=category,
            location_text=location_text,
            is_anonymous=is_anonymous,
            user_id=None if is_anonymous else current_user.id
        )

        db.session.add(issue)
        db.session.commit()
        flash('Issue reported successfully!', 'success')
        return redirect(url_for('events.home'))

    return render_template('issues/report.html')
