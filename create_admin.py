from app import create_app, db
from models import User

app = create_app()

with app.app_context():
    admin = User.query.filter_by(email='admin@communitypulse.com').first()
    if admin:
        db.session.delete(admin)
        db.session.commit()
        print("Old admin user deleted.")

    new_admin = User(
        username='admin',
        email='admin@communitypulse.com',
        role='admin',
        is_verified_organizer=True,
        is_banned=False
    )
    new_admin.set_password('123456')
    db.session.add(new_admin)
    db.session.commit()
    print("New admin user created.")
