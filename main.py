from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase
cred = credentials.Certificate("credentials.json")  # Replace with your Firebase credentials file
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://pc-db-d5bea-default-rtdb.europe-west1.firebasedatabase.app'  # Replace with your Firebase Realtime Database URL
})

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add')
def index():
    ref = db.reference('pc_parts')
    parts = ref.get() or {}
    parts_list = [{'id': key, **value} for key, value in parts.items()]
    return render_template('add.html', parts=parts_list)

def generate_unique_id():
    ref = db.reference('pc_parts')
    parts = ref.get() or {}

    # Extract existing numeric IDs and find the highest one
    max_id = 0
    for part in parts.values():
        if 'id' in part and part['id'].startswith("GPZ") and part['id'][3:].isdigit():
            num = int(part['id'][3:])
            if num > max_id:
                max_id = num

    # Increment for the next part
    new_id = f"GPZ{max_id + 1:05d}"
    return new_id

@app.route('/addpart', methods=['POST'])
def add_part():
    name = request.form['name']
    part_type = request.form['part_type']
    serial_number = request.form['serial_number']
    price = float(request.form['price'])
    audit_date = request.form['audit_date']
    part_note = str("")

    unique_id = generate_unique_id()

    ref = db.reference('pc_parts')
    new_part_ref = ref.push()
    new_part_ref.set({
        'id': unique_id,  # Unique ID is stored inside the data, not as the key
        'name': name,
        'part_type': part_type,
        'serial_number': serial_number,
        'price': price,
        'audit_date': audit_date,
        'part_note': part_note,
    })

    return redirect(url_for('index'))

@app.route('/delete/<id>')
def delete_part(id):
    ref = db.reference(f'pc_parts/{id}')
    ref.delete()
    return redirect(url_for('search_parts'))

@app.route('/edit/<id>')
def edit_page(id):
    ref = db.reference(f'pc_parts/{id}')
    part = ref.get()
    if part:
        return render_template('edit.html', part=part, id=id)
    return redirect(url_for('search_parts'))

@app.route('/update/<id>', methods=['POST'])
def update_part(id):
    ref = db.reference(f'pc_parts/{id}')
    ref.update({
        'name': request.form['name'],
        'part_type': request.form['part_type'],
        'serial_number': request.form['serial_number'],
        'price': float(request.form['price']),
        'audit_date': request.form['audit_date'],
        'part_note': request.form['part_note']
    })
    return redirect(url_for('search_parts'))

# Route for searching PC parts
@app.route('/search', methods=['GET'])
def search_parts():
    query_name = request.args.get('name', '').strip().lower()
    query_serial = request.args.get('serial_number', '').strip().lower()
    query_part_type = request.args.get('part_type', '').strip()
    query_audit_date = request.args.get('audit_date', '').strip()

    ref = db.reference('pc_parts')
    parts = ref.get() or {}

    filtered_parts = []
    for key, value in parts.items():
        name_match = query_name in value.get('name', '').lower() if query_name else True
        serial_match = query_serial in value.get('serial_number', '').lower() if query_serial else True
        type_match = value.get('part_type') == query_part_type if query_part_type else True
        date_match = value.get('audit_date') == query_audit_date if query_audit_date else True

        if name_match and serial_match and type_match and date_match:
            value['id'] = key
            filtered_parts.append(value)

    return render_template('search.html', parts=filtered_parts)

@app.route('/build_pc', methods=['GET', 'POST'])
def build_pc():
    ref = db.reference('pc_parts')
    available_parts = ref.get() or {}

    # Organize parts by type
    categorized_parts = {
        'CPU': [], 'CPU Cooler': [], 'Motherboard': [], 'RAM': [],
        'SSD': [], 'HDD': [], 'GPU': [], 'Case': [], 'PSU': []
    }

    for key, value in available_parts.items():
        if value['part_type'] in categorized_parts:
            categorized_parts[value['part_type']].append({'id': key, 'name': value['name'], 'serial_number': value['serial_number']})

    if request.method == 'POST':
        customer_details = {
            'name': request.form.get('name', 'N/A'),
            'address': request.form.get('address', 'N/A'),
            'ebay_name': request.form.get('ebay_name', 'eBay User'),
            'build_date': request.form.get('build_date', 'N/A'),
            'tracking_number': request.form.get('tracking_number', 'Pending...'),
            'sold': float(request.form.get('sold_for', 0) or 0),
            'pcid': request.form.get('pcid', 'N/A')
          
        }

        selected_parts = {}
        for part_type, options in categorized_parts.items():
            if part_type == 'RAM':  # Handle RAM separately
                ram1_id = request.form.get('ram1')
                ram2_id = request.form.get('ram2')

                if ram1_id and ram1_id in available_parts:
                    ram1_details = available_parts[ram1_id]
                    selected_parts['RAM 1'] = {
                        'id': ram1_id,
                        'gpzid': ram1_details.get('id','Unknown'),
                        'name': ram1_details.get('name', 'Unknown'),
                        'part_type': ram1_details.get('part_type', 'Unknown'),
                        'serial_number': ram1_details.get('serial_number', 'N/A'),
                        'price': ram1_details.get('price', 0),
                        'audit_date': ram1_details.get('audit_date', 'N/A'),
                        'part_note': part_details.get('part_note', 'N/A')
                    }

                if ram2_id and ram2_id in available_parts:
                    ram2_details = available_parts[ram2_id]
                    selected_parts['RAM 2'] = {
                        'id': ram2_id,
                        'gpzid': ram2_details.get('id','Unknown'),
                        'name': ram2_details.get('name', 'Unknown'),
                        'part_type': ram2_details.get('part_type', 'Unknown'),
                        'serial_number': ram2_details.get('serial_number', 'N/A'),
                        'price': ram2_details.get('price', 0),
                        'audit_date': ram2_details.get('audit_date', 'N/A'),
                        'part_note': part_details.get('part_note', 'N/A')
                    }
            else:
                part_id = request.form.get(part_type.lower().replace(' ', '_'))
                if part_id and part_id in available_parts:
                    part_details = available_parts[part_id]
                    selected_parts[part_type] = {
                        'id': part_id,
                        'gpzid': part_details.get('id','Unknown'),
                        'name': part_details.get('name', 'Unknown'),
                        'part_type': part_details.get('part_type', 'Unknown'),
                        'serial_number': part_details.get('serial_number', 'N/A'),
                        'price': part_details.get('price', 0),
                        'audit_date': part_details.get('audit_date', 'N/A'),
                        'part_note': part_details.get('part_note', 'N/A')
                    }

        # Save selected parts and customer details to pc_builds
        build_ref = db.reference('pc_builds')
        new_build_ref = build_ref.push()
        new_build_ref.set({'customer_details': customer_details, 'selected_parts': selected_parts})

        # Remove selected parts from inventory
        for part in selected_parts.values():
            db.reference(f'pc_parts/{part["id"]}').delete()

        return redirect(url_for('build_pc'))  # Reload after saving

    return render_template('build.html', parts=categorized_parts)

@app.route('/view_builds', methods=['GET'])
def view_builds():
    ref = db.reference('pc_builds')
    builds = ref.get() or {}

    builds_list = []
    for build_id, build in builds.items():
        customer_details = build.get('customer_details', {})
        build_data = {
            'build_id': build_id,
            'pc_id': customer_details.get('pcid', 'N/A'),
            'customer_name': customer_details.get('name', 'N/A'),
            'ebay_name': customer_details.get('ebay_name', 'N/A'),
            'sold_for': customer_details.get('sold', 'N/A'),
            'build_date': customer_details.get('build_date', 'N/A')
        }
        builds_list.append(build_data)

    return render_template('pc_list.html', builds=builds_list)

@app.route('/build_details/<build_id>', methods=['GET'])
def build_details(build_id):
    ref = db.reference(f'pc_builds/{build_id}')
    build = ref.get() or {}

    customer_details = build.get('customer_details', {})
    selected_parts = build.get('selected_parts', {})

    total_cost = sum(part["price"] for part in selected_parts.values())

    return render_template('build_details.html', build_id=build_id, customer_details=customer_details, selected_parts=selected_parts, total_cost=total_cost)

@app.route('/update_customer/<build_id>', methods=['GET', 'POST'])
def update_customer(build_id):
    ref = db.reference(f'pc_builds/{build_id}/customer_details')  # Reference customer details
    customer_details = ref.get()  # Fetch current customer details

    if not customer_details:
        return "Customer not found", 404

    if request.method == 'POST':
        # Get updated details from form input
        updated_data = {
            'pcid': request.form.get('pcid', ''),
            'name': request.form.get('name', ''),
            'ebay_name': request.form.get('ebay_name', ''),
            'sold': float(request.form.get('sold_for', 0)),  # Ensure float type
            'build_date': request.form.get('build_date', ''),
            'address': request.form.get('address', ''),
            'tracking_number': request.form.get('tracking_number', ''),
        }

        ref.update(updated_data)  # Update in Firebase
        return redirect(url_for('build_details', build_id=build_id))  # Redirect back to build details

    return render_template('update_customer.html', customer_details=customer_details, build_id=build_id)

if __name__ == '__main__':
    app.run(debug=True)
