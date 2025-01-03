from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import secrets
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secure random key for session management

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Returns:
        conn: SQLite connection object
    """
    conn = sqlite3.connect("fyay.db", timeout=10)
    conn.row_factory = sqlite3.Row  
    return conn

@app.route('/')
def index():
    """
    Home route displaying all events.
    Highlights events that the user has already applied to.
    """
    conn = get_db_connection()

    # Fetch all events
    events = conn.execute('SELECT * FROM events').fetchall()

    # Determine which events the user has applied to
    applied_event_ids = []
    if 'user_id' in session:
        applied_events = conn.execute(
            'SELECT event_id FROM purchases WHERE user_id = ?', (session['user_id'],)
        ).fetchall()
        applied_event_ids = [row['event_id'] for row in applied_events]

    # Enrich events with an "is_applied" flag
    enriched_events = [
        {**event, 'is_applied': event['id'] in applied_event_ids}
        for event in events
    ]

    conn.close()
    return render_template('index.html', events=enriched_events)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    Validates user input and creates a new user if valid.
    """
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        error_messages = []

        # Validate input fields
        if not full_name:
            error_messages.append("Full Name is required.")
        if not email:
            error_messages.append("Email is required.")
        elif '@' not in email or '.' not in email:
            error_messages.append("Invalid email format.")
        if not password:
            error_messages.append("Password is required.")
        elif len(password) < 6:
            error_messages.append("Password must be at least 6 characters long.")

        if error_messages:
            for error in error_messages:
                flash(error, 'danger')
            return redirect(url_for('register'))

        # Hash the password for secure storage
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)',
                (full_name, email, password_hash)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    Validates credentials and starts a session if successful.
    """
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        error_messages = []

        # Validate input fields
        if not email:
            error_messages.append("Email is required.")
        elif '@' not in email or '.' not in email:
            error_messages.append("Invalid email format.")
        if not password:
            error_messages.append("Password is required.")

        if error_messages:
            for error in error_messages:
                flash(error, 'danger')
            return redirect(url_for('login'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            # Store user details in session
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['user_email'] = user['email']
            session['user_name'] = user['full_name']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    Logs the user out and clears their session.
    """
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/apply_event/<int:event_id>', methods=['GET', 'POST'])
def apply_event(event_id):
    """
    Allows a user to apply for an event.
    Validates input and stores the application in the database.
    """
    if 'user_id' not in session:
        flash('Please log in to apply for an event.', 'warning')
        return redirect(url_for('login'))

    conn = get_db_connection()
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()

    if not event:
        flash('Event not found.', 'danger')
        conn.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_id = session['user_id']
        hours = request.form.get('hours', '').strip()
        date = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()

        error_messages = []

        # Validate form fields
        if not date:
            error_messages.append("Event Date is required.")
        elif date < event['date']:
            error_messages.append("You cannot apply for an event scheduled in the past.")

        if not hours or not hours.isdigit() or int(hours) <= 0:
            error_messages.append("Number of Hours must be a positive integer.")

        if error_messages:
            for error in error_messages:
                flash(error, 'danger')
            return redirect(url_for('apply_event', event_id=event_id))

        try:
            # Insert application into the database
            conn.execute(
                'INSERT INTO purchases (user_id, event_id, hours, description) VALUES (?, ?, ?, ?)',
                (user_id, event_id, hours, description)
            )
            conn.commit()
            flash('Successfully applied for the event!', 'success')
        except sqlite3.Error as e:
            flash(f"An error occurred while processing your application: {e}", 'danger')
        finally:
            conn.close()

        return redirect(url_for('index'))

    conn.close()
    return render_template('apply_event.html', event=event)



@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    accounts = conn.execute('''
        SELECT users.id AS user_id, users.full_name, users.email, users.role,
               GROUP_CONCAT(events.event_name || " (" || purchases.hours || " hours on " || purchases.created_at || ")") AS events_applied
        FROM users
        LEFT JOIN purchases ON users.id = purchases.user_id
        LEFT JOIN events ON purchases.event_id = events.id
        GROUP BY users.id
    ''').fetchall()

    events = conn.execute('SELECT * FROM events').fetchall()
    inventory = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()

    return render_template('admin_dashboard.html', accounts=accounts, events=events, inventory=inventory)


@app.route('/admin/place_order', methods=['GET', 'POST'])
def place_order():
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()

    if request.method == 'POST':
        # Retrieve form data
        product_name = request.form.get('product_name', '').strip()
        quantity = request.form.get('quantity', '').strip()
        price_per_unit = request.form.get('price_per_unit', '').strip()
        description = request.form.get('description', '').strip()

        # Error messages list
        error_messages = []

        # Validate fields
        if not product_name:
            error_messages.append("Product Name is required.")
        if not quantity or not quantity.isdigit() or int(quantity) <= 0:
            error_messages.append("Quantity must be a positive integer.")
        if not price_per_unit or not price_per_unit.replace('.', '', 1).isdigit() or float(price_per_unit) <= 0:
            error_messages.append("Price Per Unit must be a positive number.")

        # If there are errors, flash them and redirect to the form
        if error_messages:
            for error in error_messages:
                flash(error, 'danger')
            return redirect(url_for('place_order'))

        # Process the order
        quantity = int(quantity)
        price_per_unit = float(price_per_unit)

        # Check if the product already exists in the inventory (case-insensitive)
        existing_product = conn.execute(
            'SELECT * FROM inventory WHERE LOWER(product_name) = LOWER(?)', (product_name,)
        ).fetchone()

        if existing_product:
            # Update the existing product's quantity and price per unit
            conn.execute(
                'UPDATE inventory SET quantity = quantity + ?, price_per_unit = ? WHERE id = ?',
                (quantity, price_per_unit, existing_product['id'])
            )
        else:
            # Add a new product if it doesn't exist
            conn.execute(
                'INSERT INTO inventory (product_name, quantity, price_per_unit, description) VALUES (?, ?, ?, ?)',
                (product_name, quantity, price_per_unit, description)
            )

        # Log the order in the orders table
        conn.execute(
            'INSERT INTO orders (product_name, quantity, price_per_unit, total_price, description, date) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)',
            (product_name, quantity, price_per_unit, quantity * price_per_unit, description)
        )

        conn.commit()
        conn.close()

        flash('Order placed successfully and inventory updated.', 'success')
        return redirect(url_for('place_order'))

    # Retrieve all orders to display
    orders = conn.execute('SELECT * FROM orders ORDER BY date DESC').fetchall()
    conn.close()

    return render_template('place_order.html', orders=orders)

@app.route('/admin/create_event', methods=['GET', 'POST'])
def create_event():
    """
    Admin route to create a new event.
    Validates input and ensures selected inventory items and quantities are valid.
    """
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    with get_db_connection() as conn:
        # Fetch available inventory items with quantities greater than 0
        inventory = conn.execute('SELECT * FROM inventory WHERE quantity > 0').fetchall()

        if request.method == 'POST':
            # Collect form data
            event_name = request.form.get('event_name', '').strip()
            description = request.form.get('description', '').strip()
            location = request.form.get('location', '').strip()
            event_date = request.form.get('event_date', '').strip()
            selected_products = request.form.getlist('products')  # Selected product IDs

            # Error messages list
            error_messages = []

            # Validate required fields
            if not event_name:
                error_messages.append("Event Name is required.")
            if not description:
                error_messages.append("Description is required.")
            if not location:
                error_messages.append("Location is required.")
            if not event_date:
                error_messages.append("Event Date is required.")
            if not selected_products:
                error_messages.append("At least one product must be selected.")

            # Validate quantities for selected products
            valid_products = []
            for product_id in selected_products:
                try:
                    quantity_input_name = f'quantity_{product_id}'  # Match selected product ID to its quantity
                    quantity = request.form.get(quantity_input_name, '').strip()

                    if not quantity.isdigit() or int(quantity) <= 0:
                        error_messages.append(f"Invalid or missing quantity for product ID {product_id}.")
                        continue

                    # Fetch the inventory item to check stock
                    inventory_item = conn.execute('SELECT * FROM inventory WHERE id = ?', (product_id,)).fetchone()
                    if not inventory_item:
                        error_messages.append(f"Product ID {product_id} does not exist.")
                        continue

                    if int(quantity) > inventory_item['quantity']:
                        error_messages.append(
                            f"Insufficient stock for product '{inventory_item['product_name']}' (only {inventory_item['quantity']} available)."
                        )
                    else:
                        valid_products.append((product_id, int(quantity)))

                except ValueError:
                    error_messages.append(f"Invalid quantity for product ID {product_id}.")

            # If there are errors, flash them and return to the form
            if error_messages:
                for error in error_messages:
                    flash(error, 'danger')
                return redirect(url_for('create_event'))

            # Insert the event into the database
            conn.execute(
                'INSERT INTO events (event_name, description, location, date, created_by) VALUES (?, ?, ?, ?, ?)',
                (event_name, description, location, event_date, session['user_id'])
            )
            event_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

            # Deduct inventory and log transactions
            for product_id, quantity in valid_products:
                conn.execute(
                    'INSERT INTO inventoryTransactions (product_id, quantity_change, event_id, transaction_type) VALUES (?, ?, ?, ?)',
                    (product_id, -quantity, event_id, 'deduct')
                )
                conn.execute(
                    'UPDATE inventory SET quantity = quantity - ? WHERE id = ?',
                    (quantity, product_id)
                )

            conn.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('create_event.html', inventory=inventory)





@app.route('/admin/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()

    # Check if the event exists
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    if not event:
        flash('Event not found.', 'danger')
        conn.close()
        return redirect(url_for('admin_dashboard'))

    # Get the products used in the event
    used_products = conn.execute(
        'SELECT product_id, quantity_change FROM inventoryTransactions WHERE event_id = ? AND transaction_type = "deduct"',
        (event_id,)
    ).fetchall()

    # Restock the inventory
    for product in used_products:
        conn.execute(
            'UPDATE inventory SET quantity = quantity + ? WHERE id = ?',
            (abs(product['quantity_change']), product['product_id'])
        )

    # Delete the event and associated transactions
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.execute('DELETE FROM inventoryTransactions WHERE event_id = ?', (event_id,))
    conn.commit()
    conn.close()

    flash('Event and associated inventory adjustments have been deleted.', 'success')
    return redirect(url_for('admin_dashboard'))



@app.route('/admin/delete_inventory/<int:inventory_id>', methods=['POST'])
def delete_inventory(inventory_id):
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    with get_db_connection() as conn:
        # Check if the inventory item exists
        inventory_item = conn.execute('SELECT * FROM inventory WHERE id = ?', (inventory_id,)).fetchone()
        if not inventory_item:
            flash('Inventory item not found.', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Proceed with deletion
        conn.execute('DELETE FROM inventory WHERE id = ?', (inventory_id,))
        conn.commit()

    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    with get_db_connection() as conn:
        # Check if the order exists
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('place_order'))

        # Proceed with deletion
        conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()

    flash('Order deleted successfully!', 'success')
    return redirect(url_for('place_order'))


@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('user_role') != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    # Safeguard to prevent deleting your own account
    if user_id == session['user_id']:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin_dashboard'))

    with get_db_connection() as conn:
        # Check if the user exists
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Proceed with deletion
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))



if __name__ == "__main__":
    app.run(debug=True)
