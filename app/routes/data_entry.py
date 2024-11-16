from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import UserData, UserName, Location
from datetime import datetime

data_entry = Blueprint('data_entry', __name__)

@data_entry.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        datetime_str = request.form.get('date')
        cash_amount = float(request.form.get('cash_amount'))
        others = float(request.form.get('others'))

        datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%d')

        # Check for duplicate data based on name, location, and date
        existing_entry = UserData.query.filter_by(name=name, location=location, datetime=datetime_obj).first()
        if existing_entry:
            flash("Data Already Present For Same Date Name and Location", "warning")
            return redirect(url_for('data_entry.index'))

        new_entry = UserData(name=name, location=location, datetime=datetime_obj, cash_amount=cash_amount, others=others)
        db.session.add(new_entry)
        db.session.commit()
        flash("Data saved successfully.", "success")
        return redirect(url_for('data_entry.index'))

    names = UserName.query.all()
    locations = [location.name for location in Location.query.all()]
    return render_template('index.html', names=[name.name for name in names], locations=locations)
