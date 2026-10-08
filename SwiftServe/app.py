from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "swiftserve_ultra_key"

# --- DATA ---
# In a real app, these would be in a database (SQLAlchemy)
users = {"admin": "admin123"}
menu_items = [
    {"id": 1, "name": "Chicken Sandwich", "price": 45},
    {"id": 2, "name": "Veg Burger", "price": 35},
    {"id": 3, "name": "Fruit Juice", "price": 20}
]
orders = []

# --- HOME ---
@app.route('/')
def home(): 
    return render_template('home.html')

# --- LOGIN & REGISTRATION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if u in users and users[u] == p:
            session['user'] = u
            if u == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('menu'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u and p:
            users[u] = p
            return redirect(url_for('login'))
        return "Registration failed. Please fill all fields."
    return render_template('register.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        if u == "admin" and p == "admin123":
            session['user'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        return "Invalid Credentials. <a href='/admin_login'>Try again</a>"
    return render_template('admin_login.html')

# --- STUDENT MENU & CART ---
@app.route('/menu')
def menu():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('menu.html', items=menu_items)

@app.route('/view_cart')
def view_cart():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('view_cart.html')

# --- CHECKOUT & STATUS ---
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user' not in session: return jsonify({"status": "error"}), 401
    
    data = request.get_json()
    cart_data = data.get('cart', [])
    if not cart_data: return jsonify({"status": "error"}), 400

    total_price = sum(item['price'] * item['quantity'] for item in cart_data)
    now = datetime.now()
    
    new_order = {
        "id": len(orders) + 1,
        "user": session['user'],
        "food_list": [f"{i['name']} (x{i['quantity']})" for i in cart_data],
        "total": total_price,
        "status": "Pending",
        "time": now.strftime("%I:%M %p"),
        "timestamp": now.isoformat()
    }
    orders.append(new_order)
    return jsonify({"status": "success", "order_id": new_order['id']})

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    order = next((o for o in orders if o['id'] == order_id), None)
    return render_template('order_success.html', order=order)

@app.route('/check_status/<int:order_id>')
def check_status(order_id):
    order = next((o for o in orders if o['id'] == order_id), None)
    if order:
        return jsonify({"status": order['status']})
    return jsonify({"status": "unknown"}), 404

# --- ADMIN DASHBOARD ---
@app.route('/admin')
def admin_dashboard():
    if session.get('user') != 'admin':
        return redirect(url_for('admin_login'))
    # Passing both orders and items to the template
    return render_template('admin.html', orders=orders[::-1], items=menu_items)

# --- MENU MANAGEMENT ROUTES ---
@app.route('/add_menu', methods=['POST'])
def add_menu():
    if session.get('user') != 'admin': return "Access Denied", 403
    name = request.form.get('food_name')
    price = int(request.form.get('price'))
    # Create unique ID based on max existing ID
    new_id = max([item['id'] for item in menu_items], default=0) + 1
    menu_items.append({"id": new_id, "name": name, "price": price})
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_menu/<int:item_id>', methods=['POST'])
def edit_menu(item_id):
    if session.get('user') != 'admin': return redirect(url_for('admin_login'))
    new_name = request.form.get('name')
    new_price = int(request.form.get('price'))
    
    for item in menu_items:
        if item['id'] == item_id:
            item['name'] = new_name
            item['price'] = new_price
            break
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_menu/<int:item_id>')
def delete_menu(item_id):
    if session.get('user') != 'admin': return redirect(url_for('admin_login'))
    global menu_items
    menu_items = [item for item in menu_items if item['id'] != item_id]
    return redirect(url_for('admin_dashboard'))

@app.route('/update_status/<int:order_id>/<string:status>')
def update_status(order_id, status):
    if session.get('user') != 'admin': return "Access Denied", 403
    for order in orders:
        if order['id'] == order_id: 
            order['status'] = status
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)