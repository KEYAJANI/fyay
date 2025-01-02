# Fyay Flowers

#### Video Demo: [https://youtu.be/8rkuiTr4HGE](https://youtu.be/8rkuiTr4HGE)

### Description

Fyay is a dynamic and intuitive event management platform designed to simplify the process of organizing and managing events. Built as a final project for CS50x, it utilizes Python, Flask, SQLite3, HTML, Bootstrap, and Jinja to deliver a user-friendly experience for both event participants and administrators.

### How to Run the Project

1. Clone this repository:

   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:

   ```bash
   python database.py
   ```

4. Run the Flask application:

   ```bash
   python app.py
   ```

5. Open the application in your browser:
   ```
   http://127.0.0.1:5000/
   ```

### Features

#### User Functionality:

- Browse and view available events on a visually appealing index page.
- Apply for events using a simple application form requiring personal details, event preferences, and optional descriptions.
- Secure login and registration for personalized access.

#### Admin Functionality:

- Create new events and deduct inventory quantities based on selected products.
- Manage orders by adding product details, such as name, quantity, price per unit, and optional notes.
- Monitor and update inventory dynamically when events use or restock products.
- Delete events with automatic inventory restocking.
- Access an admin dashboard for:
  - Managing user accounts.
  - Viewing event applications.
  - Overseeing event logistics.

### Unique Features

- Real-time inventory adjustments when events are created or deleted.
- Automatic database constraints like cascading deletes to maintain data integrity.

### Database Schema

The project uses SQLite3 with the following tables:

- **users**: Stores user details (id, full_name, email, password, role).
- **events**: Stores event details (id, event_name, description, location, date).
- **purchases**: Tracks user applications for events.
- **inventory**: Tracks products, quantities, and pricing.
- **inventoryTransactions**: Logs inventory changes for events.

### Purpose

Fyay simplifies event management by integrating user applications, inventory control, and event logistics into a single platform. Its design aims to reduce manual effort for organizers while providing a seamless experience for users.

### Aesthetic

The project employs a professional color palette to enhance user experience:

- **Primary Colors**: #F7AD4E, #d69031, #4f3512
- **Accent Colors**: #FFCC80, #966d25
- **Text and Background**: #333333, #FFFFFF, #f5f5f5

### Testing and Limitations

#### Testing:

- The project was tested on both desktop and mobile browsers for responsiveness.
- All routes were tested with valid and invalid inputs.

#### Limitations:

- The platform assumes a single admin user for simplicity.
- Inventory restocking after event deletion relies on accurate transaction logs.

### Future Improvements

- Implement role-based access control for multiple administrators.
- Enhance reporting capabilities with detailed event analytics.
- Add email notifications for event confirmations and updates.

Fyay represents a blend of practical functionality and efficient design, offering a streamlined experience for users and administrators alike.

Created by Karrar Esbeyajani
