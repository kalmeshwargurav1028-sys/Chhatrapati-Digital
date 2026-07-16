import os
import sqlite3
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DATABASE = 'inquiries.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'New'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                last_login DATETIME,
                avatar TEXT,
                username TEXT,
                role TEXT,
                date_joined DATETIME,
                bio TEXT
            )
        ''')
        
        # Safely add columns if they don't exist (SQLite ALTER TABLE limitation workaround)
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN phone TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN last_login DATETIME")
        except: pass
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN username TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN role TEXT")
        except: pass
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN date_joined DATETIME")
        except: pass
        try: cursor.execute("ALTER TABLE admin_profile ADD COLUMN bio TEXT")
        except: pass

        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                review_text TEXT,
                video_path TEXT,
                status TEXT DEFAULT 'Pending',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pricing_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price TEXT NOT NULL,
                features TEXT NOT NULL,
                is_popular INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                category TEXT NOT NULL,
                image_url TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS our_story (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                paragraph TEXT NOT NULL,
                stats TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                po_num TEXT NOT NULL,
                total REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS client_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Auto-migrate: add work_process column to portfolio if it doesn't exist
        try:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN work_process TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass # Column likely already exists
        
        # Seed initial admin profile if empty
        cursor.execute("SELECT COUNT(*) FROM admin_profile")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO admin_profile (name, email, username, role, date_joined) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", ("Rao Chethan", "raochethan604@gmail.com", "rao.chethan", "Super Admin"))
            
        # Seed CMS data if empty
        cursor.execute("SELECT COUNT(*) FROM pricing_packages")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO pricing_packages (name, price, features, is_popular) VALUES (?, ?, ?, ?)", ('Basic Branding', '₹4,999', 'Logo Design (2 Concepts)|Business Card Design|Social Media Kit (3 Posts)', 0))
            cursor.execute("INSERT INTO pricing_packages (name, price, features, is_popular) VALUES (?, ?, ?, ?)", ('Pro Photography', '₹14,999', 'Full Day Event Coverage|Cinematic Video Edit|50+ Edited Photos', 1))
            cursor.execute("INSERT INTO pricing_packages (name, price, features, is_popular) VALUES (?, ?, ?, ?)", ('Premium Signage', 'Custom', '3D LED Letters|Neon Board Design|Complete Installation', 0))

        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO services (icon, title, description) VALUES (?, ?, ?)", ('fa-paint-brush', 'Graphic Design & Branding', 'Logos, business cards, social media posts, and complete brand identity packages.'))
            cursor.execute("INSERT INTO services (icon, title, description) VALUES (?, ?, ?)", ('fa-sign', 'Premium Signage (LED & 3D)', 'Eye-catching glow signs, neon boards, 3D acrylic letters, and flex banners.'))
            cursor.execute("INSERT INTO services (icon, title, description) VALUES (?, ?, ?)", ('fa-camera', 'Event Photography & Video', 'Cinematic coverage for weddings, corporate events, and product shoots.'))
            cursor.execute("INSERT INTO services (icon, title, description) VALUES (?, ?, ?)", ('fa-laptop-code', 'Web Development', 'Custom websites, e-commerce stores, and SEO optimization.'))
            
        cursor.execute("SELECT COUNT(*) FROM portfolio")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Wedding Photography', 'photography', '/static/assets/wedding_photography_1784128887323.png'))
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Logo Design', 'branding', '/static/assets/graphic_design_logo_1784128898227.png'))
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Signage Solutions', 'signage', '/static/assets/neon_signage_1784128909986.png'))
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Event Photography', 'photography', 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?q=80&w=2069&auto=format&fit=crop'))
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Brand Identity', 'branding', 'https://images.unsplash.com/photo-1626785774573-4b799315345d?q=80&w=2071&auto=format&fit=crop'))
            cursor.execute("INSERT INTO portfolio (project_name, category, image_url) VALUES (?, ?, ?)", ('Neon Design', 'signage', 'https://images.unsplash.com/photo-1563203369-26f2e4a5ccf7?q=80&w=2070&auto=format&fit=crop'))

        cursor.execute("SELECT COUNT(*) FROM our_story")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO our_story (headline, paragraph, stats) VALUES (?, ?, ?)", ('Who We Are', 'Founded in the heart of the city, Chhatrapati Digital started with a simple mission: to help local businesses shine brighter. From crafting a simple logo to installing massive 3D glowing storefronts, we combine artistry with technology to deliver results that wow your customers.', '150+|Projects Delivered,15+|Years Combined Exp,50+|5-Star Reviews'))

        db.commit()

# Initialize DB on startup
init_db()

def send_email_notification(inquiry_id, service, details):
    sender_email = "agent4@indusschool.com"
    sender_password = "Agent@2026"
    receiver_email = "agent4@indusschool.com"

    subject = f"NEW INQUIRY: {service}"
    body = f"--- NEW INQUIRY [{service}] ---\nID: #{inquiry_id}\nTime: {datetime.now().isoformat()}\nDetails: {details}\n-------------------------------\n"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print(f"Email sent successfully for Inquiry #{inquiry_id}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # fallback to outbox
        with open('email_outbox.txt', 'a') as f:
            f.write(f"FAILED TO SEND EMAIL. Error: {e}\n")
            f.write(body + "\n\n")

def sync_to_spreadsheet(inquiry_id, service, details):
    file_exists = os.path.isfile('inquiries_sync.csv')
    with open('inquiries_sync.csv', 'a', newline='') as csvfile:
        fieldnames = ['ID', 'Timestamp', 'Service', 'Details', 'Status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'ID': inquiry_id,
            'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Service': service,
            'Details': details,
            'Status': 'New'
        })

@app.route('/')
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM reviews WHERE status = 'Approved' ORDER BY timestamp DESC")
    reviews = cursor.fetchall()
    
    cursor.execute("SELECT * FROM pricing_packages")
    pricing = cursor.fetchall()
    
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    
    cursor.execute("SELECT * FROM portfolio")
    portfolio = cursor.fetchall()
    
    cursor.execute("SELECT * FROM our_story LIMIT 1")
    story = cursor.fetchone()
    
    # Process features and stats for easy rendering
    pricing_processed = []
    for p in pricing:
        pd = dict(p)
        pd['features_list'] = pd['features'].split('|')
        pricing_processed.append(pd)
        
    story_processed = dict(story) if story else {}
    if story_processed:
        # Split "150+|Projects,15+|Years" into pairs
        stats_raw = story_processed['stats'].split(',')
        story_processed['stats_list'] = []
        for s in stats_raw:
            if '|' in s:
                val, label = s.split('|')
                story_processed['stats_list'].append({'val': val, 'label': label})
    
    return render_template('index.html', reviews=reviews, pricing=pricing_processed, services=services, portfolio=portfolio, story=story_processed)

@app.route('/api/order', methods=['POST'])
def submit_order():
    data = request.json
    service = data.get('service')
    details = data.get('details')
    
    if not service or not details:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO inquiries (service, details) VALUES (?, ?)", (service, details))
    inquiry_id = cursor.lastrowid
    
    # Add notification
    cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("NEW INQUIRY", f"#{inquiry_id} - {service}"))
    db.commit()
    
    # Simulate real-time email notification
    send_email_notification(inquiry_id, service, details)
    
    # Simulate real-time spreadsheet sync
    sync_to_spreadsheet(inquiry_id, service, details)
    
    return jsonify({"status": "success", "message": "Order submitted successfully! We will contact you soon."})

@app.route('/admin/inquiries')
def admin_inquiries():
    db = get_db()
    cursor = db.cursor()
    
    # Get inquiries
    cursor.execute("SELECT * FROM inquiries ORDER BY timestamp DESC")
    inquiries = cursor.fetchall()
    
    # Get profile
    cursor.execute("SELECT * FROM admin_profile LIMIT 1")
    profile = cursor.fetchone()
    
    # Get reviews
    cursor.execute("SELECT * FROM reviews ORDER BY timestamp DESC")
    reviews = cursor.fetchall()
    
    # Get CMS Data for Admin
    cursor.execute("SELECT * FROM pricing_packages")
    pricing = cursor.fetchall()
    cursor.execute("SELECT * FROM services")
    services = cursor.fetchall()
    cursor.execute("SELECT * FROM portfolio")
    portfolio = cursor.fetchall()
    cursor.execute("SELECT * FROM our_story LIMIT 1")
    story = cursor.fetchone()
    if story:
        stats_raw = story['stats'].split('|')
        stats_list = [{'val': s.split(':')[0], 'label': s.split(':')[1]} for s in stats_raw if ':' in s]
        story = dict(story)
        story['stats_list'] = stats_list
    cms_data = {
        'pricing': pricing,
        'services': services,
        'portfolio': portfolio,
        'story': story
    }
    
    # Get invoices history
    cursor.execute("SELECT * FROM invoices ORDER BY timestamp DESC")
    invoices = cursor.fetchall()
    
    # Calculate simple metrics
    total_inquiries = len(inquiries)
    pending_review = sum(1 for i in inquiries if i['status'] in ('New', 'Pending'))
    active_projects = sum(1 for i in inquiries if i['status'] == 'Active Project')
    completed_projects = sum(1 for i in inquiries if i['status'] == 'Completed')
    
    # Get client tickets
    cursor.execute("SELECT * FROM client_tickets ORDER BY timestamp DESC")
    tickets = [dict(row) for row in cursor.fetchall()]
    
    if total_inquiries > 0:
        conversion_rate = round(((active_projects + completed_projects) / total_inquiries) * 100, 1)
    else:
        conversion_rate = 0.0
        
    metrics = {
        "total": total_inquiries,
        "pending": pending_review,
        "active": active_projects,
        "conversion": conversion_rate,
        "total_tickets": len(tickets),
        "unresolved_tickets": sum(1 for t in tickets if t['status'] != 'Resolved')
    }
    
    return render_template('admin_dashboard.html', inquiries=inquiries, reviews=reviews, metrics=metrics, profile=profile, cms=cms_data, invoices=invoices, tickets=tickets)

@app.route('/api/profile', methods=['GET', 'POST'])
def handle_profile():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bio = request.form.get('bio')
        
        # Check if an avatar file was uploaded
        avatar_path = None
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                # Store the web-accessible URL
                avatar_path = '/static/uploads/' + filename
                
        # If a file was uploaded, update the avatar column, else keep it unchanged
        if avatar_path:
            cursor.execute("UPDATE admin_profile SET name = ?, email = ?, phone = ?, avatar = ?, bio = ? WHERE id = 1", (name, email, phone, avatar_path, bio))
        else:
            cursor.execute("UPDATE admin_profile SET name = ?, email = ?, phone = ?, bio = ? WHERE id = 1", (name, email, phone, bio))
            
        db.commit()
        
        # Also conditionally update the DB's seed email since user asked to "remove that email and add raochethan604@gmail.com"
        # The form submission handles email updates normally, but we will force update it here if the user's request meant to globally reset it.
        # It's already handled via request.form.get('email').

        return jsonify({"status": "success", "avatar": avatar_path})
        
    cursor.execute("SELECT * FROM admin_profile LIMIT 1")
    profile = dict(cursor.fetchone())
    return jsonify({"status": "success", "profile": profile})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifications ORDER BY timestamp DESC LIMIT 5")
    notifications = [dict(row) for row in cursor.fetchall()]
    return jsonify({"status": "success", "notifications": notifications})

@app.route('/api/inquiries/<int:inquiry_id>/status', methods=['POST'])
def update_inquiry_status(inquiry_id):
    data = request.json
    new_status = data.get('status')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE inquiries SET status = ? WHERE id = ?", (new_status, inquiry_id))
    
    email_dispatched = False
    if new_status == 'Active Project':
        # Simulate sending automated welcome email
        cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("AUTOMATED EMAIL", f"Welcome packet sent for #{inquiry_id}"))
        email_dispatched = True
        
        with open('email_outbox.txt', 'a') as f:
            f.write(f"--- AUTOMATED WELCOME EMAIL ---\n")
            f.write(f"To: Inquiry #{inquiry_id}\n")
            f.write(f"Subject: Welcome to Chhatrapati Digital - Next Steps\n")
            f.write(f"Body: Hello! We are thrilled to start working on your project. Here is your welcome packet and timeline...\n")
            f.write("-------------------------------\n\n")
            
    db.commit()
    return jsonify({"status": "success", "email_dispatched": email_dispatched})

@app.route('/api/inquiries/<int:inquiry_id>/action', methods=['POST'])
def execute_inquiry_action(inquiry_id):
    data = request.json
    action_type = data.get('action_type')
    details = data.get('details')
    
    db = get_db()
    cursor = db.cursor()
    
    if action_type == 'quote':
        msg = f"Generated Quote: {details}"
        cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("QUOTE SENT", f"#{inquiry_id} - ₹{details.get('cost')}"))
    elif action_type == 'email':
        msg = f"Sent Email: {details}"
        cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("EMAIL SENT", f"#{inquiry_id}"))
    elif action_type == 'consultation':
        msg = "Scheduled Consultation"
        cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("CONSULTATION", f"#{inquiry_id}"))
        cursor.execute("UPDATE inquiries SET status = 'Contacted' WHERE id = ?", (inquiry_id,))
        
    db.commit()
    
    with open('email_outbox.txt', 'a') as f:
        f.write(f"--- ACTION PERFORMED ON #{inquiry_id} ---\n")
        f.write(f"Type: {action_type}\n")
        f.write(f"Details: {details}\n")
        f.write("-------------------------------\n\n")
        
    return jsonify({"status": "success"})

@app.route('/leave-review', methods=['GET', 'POST'])
def leave_review():
    if request.method == 'POST':
        client_name = request.form.get('client_name')
        rating = request.form.get('rating')
        review_text = request.form.get('review_text')
        
        video_path = None
        if 'video_file' in request.files:
            file = request.files['video_file']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                video_path = '/static/uploads/' + filename
                
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO reviews (client_name, rating, review_text, video_path) VALUES (?, ?, ?, ?)", (client_name, rating, review_text, video_path))
        review_id = cursor.lastrowid
        cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("NEW REVIEW", f"By {client_name} - {rating} Stars"))
        db.commit()
        return render_template('leave_review.html', success=True)
        
    return render_template('leave_review.html')

@app.route('/api/reviews/<int:review_id>/status', methods=['POST'])
def update_review_status(review_id):
    data = request.json
    new_status = data.get('status')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE reviews SET status = ? WHERE id = ?", (new_status, review_id))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/cms/pricing', methods=['POST'])
def update_pricing():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    for item in data.get('packages', []):
        cursor.execute("UPDATE pricing_packages SET name = ?, price = ?, features = ?, is_popular = ? WHERE id = ?", 
                       (item['name'], item['price'], item['features'], item['is_popular'], item['id']))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/cms/services', methods=['POST'])
def update_services():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    for item in data.get('services', []):
        cursor.execute("UPDATE services SET icon = ?, title = ?, description = ? WHERE id = ?", 
                       (item['icon'], item['title'], item['description'], item['id']))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/cms/story', methods=['POST'])
def update_story():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE our_story SET headline = ?, paragraph = ?, stats = ? WHERE id = 1", 
                   (data['headline'], data['paragraph'], data['stats']))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/cms/portfolio', methods=['POST'])
def add_portfolio():
    project_name = request.form.get('project_name')
    category = request.form.get('category')
    work_process = request.form.get('work_process', '')
    
    image_url = None
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = '/static/uploads/' + filename
            
    if image_url:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO portfolio (project_name, category, image_url, work_process) VALUES (?, ?, ?, ?)", (project_name, category, image_url, work_process))
        db.commit()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No image uploaded"})

@app.route('/api/cms/portfolio/<int:item_id>', methods=['DELETE'])
def delete_portfolio(item_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ?", (item_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/invoices', methods=['POST'])
def save_invoice():
    data = request.json
    client_name = data.get('client_name')
    po_num = data.get('po_num')
    total = data.get('total')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO invoices (client_name, po_num, total) VALUES (?, ?, ?)", (client_name, po_num, total))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/pay/<po_num>')
def pay_invoice(po_num):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM invoices WHERE po_num = ? ORDER BY timestamp DESC LIMIT 1", (po_num,))
    invoice = cursor.fetchone()
    if not invoice:
        if po_num == '#CD-1001':
            invoice = {'po_num': '#CD-1001', 'client_name': 'Mock Client', 'total': 4999.00, 'timestamp': '2026-06-15'}
        else:
            return "Invoice not found.", 404
    return render_template('payment.html', invoice=invoice)

@app.route('/print/<po_num>')
def print_invoice(po_num):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM invoices WHERE po_num = ? ORDER BY timestamp DESC LIMIT 1", (po_num,))
    invoice = cursor.fetchone()
    if not invoice:
        if po_num == '#CD-1001':
            invoice = {'po_num': '#CD-1001', 'client_name': 'Mock Client', 'total': 4999.00, 'timestamp': '2026-06-15'}
        else:
            return "Invoice not found.", 404
    
    # We will just render a simple string with HTML that triggers print, 
    # since we don't have a complex itemized invoice table.
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Invoice {invoice['po_num']}</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; color: #333; }}
            .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 20px; margin-bottom: 40px; }}
            .title {{ font-size: 24px; font-weight: bold; }}
            .total {{ font-size: 20px; font-weight: bold; margin-top: 40px; border-top: 1px solid #ccc; padding-top: 20px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="header">
            <div>
                <div class="title">Chhatrapati Digital</div>
                <div>Official Invoice Receipt</div>
            </div>
            <div style="text-align: right;">
                <div><strong>Invoice #:</strong> {invoice['po_num']}</div>
                <div><strong>Date:</strong> {invoice['timestamp'].split(' ')[0]}</div>
            </div>
        </div>
        
        <div><strong>Billed To:</strong> {invoice['client_name']}</div>
        
        <table style="width: 100%; margin-top: 40px; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #ccc; text-align: left;">
                <th style="padding: 10px 0;">Description</th>
                <th style="padding: 10px 0; text-align: right;">Amount</th>
            </tr>
            <tr>
                <td style="padding: 20px 0;">Digital Agency Services</td>
                <td style="padding: 20px 0; text-align: right;">₹{invoice['total']:.2f}</td>
            </tr>
        </table>
        
        <div class="total" style="text-align: right;">Total Paid / Due: ₹{invoice['total']:.2f}</div>
        
        <div style="margin-top: 80px; text-align: center; color: #777; font-size: 12px;">
            Thank you for your business!
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/invoices/<int:invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return jsonify({"status": "success", "redirect": "/dashboard"})
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM invoices ORDER BY id DESC")
    invoices = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM client_tickets ORDER BY id DESC")
    tickets = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM inquiries ORDER BY timestamp DESC")
    inquiries = [dict(row) for row in cursor.fetchall()]
    
    return render_template('dashboard.html', invoices=invoices, tickets=tickets, inquiries=inquiries)

@app.route('/api/client/tickets', methods=['POST'])
def add_client_ticket():
    subject = request.form.get('subject')
    message = request.form.get('message')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO client_tickets (subject, message) VALUES (?, ?)", (subject, message))
    cursor.execute("INSERT INTO notifications (type, message) VALUES (?, ?)", ("SUPPORT TICKET", f"New ticket: {subject}"))
    db.commit()
    return jsonify({"status": "success"})

@app.route('/api/admin/tickets/<int:ticket_id>/resolve', methods=['POST'])
def resolve_client_ticket(ticket_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE client_tickets SET status = 'Resolved' WHERE id = ?", (ticket_id,))
    db.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
