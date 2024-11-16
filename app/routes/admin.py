from flask import Blueprint, render_template, request, session, redirect, url_for, flash, send_file
from app import db
from app.models import Admin, UserData, User, UserName, Location
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
from sqlalchemy import func, cast, Date
import csv
import tempfile
from flask import get_flashed_messages
import pytz


admin = Blueprint('admin', __name__)
local_timezone = pytz.timezone('America/Chicago')
# Admin Login
@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    # Clear all old messages to ensure only relevant messages are shown
    session.pop('_flashes', None)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['is_admin'] = True
            # flash("Successfully logged in as admin.", "success")
            return redirect(url_for('admin.dashboard'))
        flash("Invalid credentials, please try again.", "danger")
    return render_template('admin_login.html')


# Change Password
@admin.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        admin = Admin.query.first()  # Assuming a single admin system

        # Check if the current password matches
        if not admin or not admin.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for('admin.change_password'))

        # Check if the new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.", "warning")
            return redirect(url_for('admin.change_password'))

        # Update the password
        admin.set_password(new_password)
        db.session.commit()
        flash("Password updated successfully.", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('change_password.html')


# Dashboard with Filtering, Sorting, and Charts
@admin.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    start_date_full = request.form.get('start_date_full', (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    end_date_full = request.form.get('end_date_full', datetime.today().strftime('%Y-%m-%d'))
    filter_name_full = request.form.get('filter_name_full', '')
    filter_location_full = request.form.get('filter_location_full', '')
    sort_full = request.form.get('sort_full', 'datetime')

    full_data_query = UserData.query
    if filter_name_full:
        full_data_query = full_data_query.filter(UserData.name == filter_name_full)
    if filter_location_full:
        full_data_query = full_data_query.filter(UserData.location == filter_location_full)
    if start_date_full and end_date_full:
        start_date_obj = datetime.strptime(start_date_full, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date_full, '%Y-%m-%d').date()
        full_data_query = full_data_query.filter(UserData.datetime >= start_date_obj, UserData.datetime <= end_date_obj)

    if sort_full == 'total_amount':
        full_data_query = full_data_query.order_by(UserData.total_amount.desc())
    else:
        full_data_query = full_data_query.order_by(UserData.datetime.desc())

    full_data = full_data_query.all()

    names = db.session.query(UserName.name).distinct().all()  # Now using UserName table for dropdown
    locations = db.session.query(UserData.location).distinct().all()

    session['start_date'] = start_date_full
    session['end_date'] = end_date_full
    session['filter_name'] = filter_name_full
    session['filter_location'] = filter_location_full

    return render_template(
        'admin.html',
        full_data=full_data,
        names=[name[0] for name in names],
        locations=[location[0] for location in locations],
        start_date_full=start_date_full,
        end_date_full=end_date_full,
        filter_name_full=filter_name_full,
        filter_location_full=filter_location_full,
        sort_full=sort_full
    )

# Manage User Names (Add/Delete) for Dropdown
@admin.route('/manage_usernames', methods=['GET', 'POST'])
def manage_usernames():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')

        if action == 'add' and name:
            if not UserName.query.filter_by(name=name).first():
                new_user_name = UserName(name=name)
                db.session.add(new_user_name)
                db.session.commit()
                # flash("User name added successfully.", "success")
            else:
                flash("This name already exists.", "warning")

        elif action == 'delete' and name:
            user_name = UserName.query.filter_by(name=name).first()
            if user_name:
                db.session.delete(user_name)
                db.session.commit()
                # flash("User name deleted successfully.", "success")
            else:
                flash("User name not found.", "danger")

    user_names = UserName.query.all()
    return render_template('manage_usernames.html', user_names=user_names)

# Manage Users (Add/Delete)
@admin.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')

        if action == 'add_user' and name:
            if not User.query.filter_by(name=name).first():
                new_user = User(name=name)
                db.session.add(new_user)
                db.session.commit()
                # flash("User added successfully.", "success")
            else:
                flash("This user already exists.", "warning")

        elif action == 'delete_user' and name:
            user = User.query.filter_by(name=name).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                # flash("User deleted successfully.", "success")
            else:
                flash("User not found.", "danger")

    users = User.query.all()
    return render_template('manage_users.html', users=users)

# Manage Locations (Add/Delete)
@admin.route('/manage_locations', methods=['GET', 'POST'])
def manage_locations():
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')
        location = request.form.get('location')

        if action == 'add' and location:
            if not Location.query.filter_by(name=location).first():
                new_location = Location(name=location)
                db.session.add(new_location)
                db.session.commit()
                # flash("Location added successfully.", "success")
            else:
                flash("This location already exists.", "warning")

        elif action == 'delete' and location:
            existing_location = Location.query.filter_by(name=location).first()
            if existing_location:
                db.session.delete(existing_location)
                db.session.commit()
                # flash("Location deleted successfully.", "success")
            else:
                flash("Location not found.", "danger")

    locations = Location.query.all()
    return render_template('manage_locations.html', locations=locations)


# Generate Chart by Date
@admin.route('/chart_date_sum')
def chart_date_sum():
    start_date = datetime.strptime(session.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(session.get('end_date'), '%Y-%m-%d')
    filter_name = session.get('filter_name')
    filter_location = session.get('filter_location')

    date_data_query = db.session.query(
        cast(UserData.datetime, Date).label('date'),
        func.sum(UserData.total_amount).label('total_amount')
    ).filter(UserData.datetime.between(start_date, end_date))

    if filter_name:
        date_data_query = date_data_query.filter(UserData.name == filter_name)
    if filter_location:
        date_data_query = date_data_query.filter(UserData.location == filter_location)

    date_data = date_data_query.group_by(cast(UserData.datetime, Date)).all()

    dates = [str(row.date) for row in date_data]
    sums = [row.total_amount for row in date_data]

    fig, ax = plt.subplots()
    ax.bar(dates, sums)
    ax.set_xlabel("Date")
    ax.set_ylabel("Total Amount")
    ax.set_title("Total Sum by Date")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)
    return send_file(img, mimetype="image/png")


# Generate Chart by Name
@admin.route('/chart_name_sum')
def chart_name_sum():
    start_date = datetime.strptime(session.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(session.get('end_date'), '%Y-%m-%d')
    filter_location = session.get('filter_location')

    name_data_query = db.session.query(
        UserData.name,
        func.sum(UserData.total_amount).label('total_amount')
    ).filter(UserData.datetime.between(start_date, end_date))

    if filter_location:
        name_data_query = name_data_query.filter(UserData.location == filter_location)

    name_data = name_data_query.group_by(UserData.name).all()

    names = [row.name for row in name_data]
    totals = [row.total_amount for row in name_data]

    fig, ax = plt.subplots()
    ax.bar(names, totals)
    ax.set_xlabel("Name")
    ax.set_ylabel("Total Amount")
    ax.set_title("Total Amount by Name")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)
    return send_file(img, mimetype="image/png")

# Generate Chart by Location
@admin.route('/chart_location_sum')
def chart_location_sum():
    start_date = datetime.strptime(session.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(session.get('end_date'), '%Y-%m-%d')
    filter_name = session.get('filter_name')

    location_data_query = db.session.query(
        UserData.location,
        func.sum(UserData.total_amount).label('total_amount')
    ).filter(UserData.datetime.between(start_date, end_date))

    if filter_name:
        location_data_query = location_data_query.filter(UserData.name == filter_name)

    location_data = location_data_query.group_by(UserData.location).all()

    locations = [row.location for row in location_data]
    totals = [row.total_amount for row in location_data]

    fig, ax = plt.subplots()
    ax.bar(locations, totals)
    ax.set_xlabel("Location")
    ax.set_ylabel("Total Amount")
    ax.set_title("Total Amount by Location")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)
    return send_file(img, mimetype="image/png")

@admin.route('/edit_user_data/<int:user_id>', methods=['GET', 'POST'])
def edit_user_data(user_id):
    if not session.get('is_admin'):
        return redirect(url_for('admin.admin_login'))

    user_data = UserData.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user_data.name = request.form['name']
        user_data.location = request.form['location']
        
        # Parse the datetime string
        user_data.datetime = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%H:%M')
        
        user_data.cash_amount = float(request.form['cash_amount'])
        user_data.others = float(request.form['others'])
        user_data.total_amount = user_data.cash_amount + user_data.others
        user_data.updated_at = datetime.now(local_timezone)  # Update the updated_at field
        
        db.session.commit()
        flash("User data updated successfully.", "success")
        return redirect(url_for('admin.dashboard'))

    return render_template('edit_user_data.html', user_data=user_data)



@admin.route('/download_data', methods=['POST'])
def download_data():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    filename = request.form.get('filename', 'filtered_data.csv')  # Get filename from form or set default
    # if '.csv' or '.xlsx' not in filename:
    filename=filename+'.csv'
    data_query = UserData.query
    if start_date and end_date:
        data_query = data_query.filter(UserData.datetime.between(start_date, end_date))

    data = data_query.all()

    # Create a temporary CSV file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    with open(temp_file.name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Location', 'Date and Time', 'Cash Amount', 'Others', 'Total Amount'])
        for entry in data:
            writer.writerow([entry.name, entry.location, entry.datetime, entry.cash_amount, entry.others, entry.total_amount])

    return send_file(temp_file.name, as_attachment=True, download_name=filename)

# Route to delete a specific row
@admin.route('/delete_entry/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    entry = UserData.query.get(entry_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        # flash("Entry deleted successfully.", "success")
    else:
        flash("Entry not found.", "danger")
    return redirect(url_for('admin.dashboard'))

# Logout
@admin.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('admin.admin_login'))
