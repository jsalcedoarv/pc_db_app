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

    unique_id = generate_unique_id()

    ref = db.reference('pc_parts')
    new_part_ref = ref.push()
    new_part_ref.set({
        'id': unique_id,  # Unique ID is stored inside the data, not as the key
        'name': name,
        'part_type': part_type,
        'serial_number': serial_number,
        'price': price,
        'audit_date': audit_date
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
        'audit_date': request.form['audit_date']
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

if __name__ == '__main__':
    app.run(debug=True, host='192.168.0.152')
