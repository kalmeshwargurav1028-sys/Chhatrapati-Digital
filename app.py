import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template, request, jsonify, g
from werkzeug.utils import secure_filename
import pymongo
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception:
    pass

# Initialize MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://kalmeshwargurav1028_db_user:OzKo1PYkMjTN5xOR@cluster0.ipegkdw.mongodb.net/chhatrapati_digital?retryWrites=true&w=majority&appName=Cluster0")
client = pymongo.MongoClient(MONGO_URI)
db = client.chhatrapati_digital

# Initialize DB on startup
def init_db():
    # Seed initial admin profile if empty
    if db.admin_profile.count_documents({}) == 0:
        db.admin_profile.insert_one({"name": "Rao Chethan", "email": "raochethan604@gmail.com", "username": "rao.chethan", "role": "Super Admin", "date_joined": datetime.now()})
        
    # Seed CMS data if empty
    if db.pricing_packages.count_documents({}) == 0:
        db.pricing_packages.insert_many([
            {"name": 'Basic Branding', "price": '₹4,999', "features": 'Logo Design (2 Concepts)|Business Card Design|Social Media Kit (3 Posts)', "is_popular": 0},
            {"name": 'Pro Photography', "price": '₹14,999', "features": 'Full Day Event Coverage|Cinematic Video Edit|50+ Edited Photos', "is_popular": 1},
            {"name": 'Premium Signage', "price": 'Custom', "features": '3D LED Letters|Neon Board Design|Complete Installation', "is_popular": 0}
        ])

    if db.services.count_documents({}) == 0:
        db.services.insert_many([
            {"icon": 'fa-paint-brush', "title": 'Graphic Design & Branding', "description": 'Logos, business cards, social media posts, and complete brand identity packages.'},
            {"icon": 'fa-sign', "title": 'Premium Signage (LED & 3D)', "description": 'Eye-catching glow signs, neon boards, 3D acrylic letters, and flex banners.'},
            {"icon": 'fa-camera', "title": 'Event Photography & Video', "description": 'Cinematic coverage for weddings, corporate events, and product shoots.'},
            {"icon": 'fa-laptop-code', "title": 'Web Development', "description": 'Custom websites, e-commerce stores, and SEO optimization.'}
        ])
        
    if db.portfolio.count_documents({}) == 0:
        db.portfolio.insert_many([
            {"project_name": 'Wedding Photography', "category": 'photography', "image_url": '/static/assets/wedding_photography_1784128887323.png', "work_process": ""},
            {"project_name": 'Logo Design', "category": 'branding', "image_url": '/static/assets/graphic_design_logo_1784128898227.png', "work_process": ""},
            {"project_name": 'Signage Solutions', "category": 'signage', "image_url": '/static/assets/neon_signage_1784128909986.png', "work_process": ""},
            {"project_name": 'Event Photography', "category": 'photography', "image_url": 'https://images.unsplash.com/photo-1511285560929-80b456fea0bc?q=80&w=2069&auto=format&fit=crop', "work_process": ""},
            {"project_name": 'Brand Identity', "category": 'branding', "image_url": 'https://images.unsplash.com/photo-1626785774573-4b799315345d?q=80&w=2071&auto=format&fit=crop', "work_process": ""},
            {"project_name": 'Neon Design', "category": 'signage', "image_url": 'https://images.unsplash.com/photo-1563203369-26f2e4a5ccf7?q=80&w=2070&auto=format&fit=crop', "work_process": ""}
        ])

    if db.our_story.count_documents({}) == 0:
        db.our_story.insert_one({"headline": 'Who We Are', "paragraph": 'Founded in the heart of the city, Chhatrapati Digital started with a simple mission: to help local businesses shine brighter. From crafting a simple logo to installing massive 3D glowing storefronts, we combine artistry with technology to deliver results that wow your customers.', "stats": '150+|Projects Delivered,15+|Years Combined Exp,50+|5-Star Reviews'})

    if db.site_config.count_documents({}) == 0:
        db.site_config.insert_one({
            "hero_title": "Transform Your Brand with<br>High-End Digital Solutions",
            "hero_subtitle": "We create stunning designs, professional photography, and premium signage that drive sales and build trust.",
            "contact_email": "raochethan604@gmail.com",
            "contact_phone": "+91 74830 06958",
            "whatsapp_num": "917483006958",
            "instagram_link": "https://www.instagram.com/mr_drackey02?igsh=dW02NmNiYmttdDBi",
            "facebook_link": "#",
            "linkedin_link": "#"
        })

# init_db()  # Disabled on Vercel to prevent cold start timeouts

def convert_id(doc):
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
    return doc

def convert_ids(cursor):
    return [convert_id(doc) for doc in cursor]

def send_email_notification(inquiry_id, service, details):
    sender_email = "agent4@indusschool.com"
    sender_password = "Agent@2026"
    receiver_email = "raochethan604@gmail.com"

    subject = f"NEW INQUIRY: {service}"
    body = f"--- NEW INQUIRY [{service}]\nID: #{inquiry_id}\nTime: {datetime.now().isoformat()}\nDetails: {details}\n-------------------------------\n"

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
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Vercel fallback - ignore if filesystem is read-only
        try:
            with open('email_outbox.txt', 'a') as f:
                f.write(f"FAILED TO SEND EMAIL. Error: {e}\n")
                f.write(body + "\n\n")
        except Exception:
            pass

def sync_to_spreadsheet(inquiry_id, service, details):
    try:
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
    except Exception as e:
        print(f"Failed to sync to spreadsheet (likely Vercel read-only FS): {e}")

@app.route('/')
def index():
    reviews = convert_ids(db.reviews.find({"status": "Approved"}).sort("timestamp", -1))
    pricing = convert_ids(db.pricing_packages.find())
    services = convert_ids(db.services.find())
    portfolio = convert_ids(db.portfolio.find())
    story = convert_id(db.our_story.find_one())
    
    # Process features and stats for easy rendering
    pricing_processed = []
    for p in pricing:
        pd = dict(p)
        pd['features_list'] = pd['features'].split('|')
        pricing_processed.append(pd)
        
    story_processed = dict(story) if story else {}
    if story_processed:
        stats_raw = story_processed['stats'].split(',')
        story_processed['stats_list'] = []
        for s in stats_raw:
            if '|' in s:
                val, label = s.split('|')
                story_processed['stats_list'].append({'val': val, 'label': label})
                
    config = convert_id(db.site_config.find_one())
    if not config:
        # Fallback default if not seeded
        config = {
            "hero_title": "Transform Your Brand with<br>High-End Digital Solutions",
            "hero_subtitle": "We create stunning designs, professional photography, and premium signage that drive sales and build trust.",
            "contact_email": "raochethan604@gmail.com",
            "contact_phone": "+91 74830 06958",
            "whatsapp_num": "917483006958",
            "instagram_link": "https://www.instagram.com/mr_drackey02?igsh=dW02NmNiYmttdDBi",
            "facebook_link": "#",
            "linkedin_link": "#"
        }
    
    return render_template('index.html', reviews=reviews, pricing=pricing_processed, services=services, portfolio=portfolio, story=story_processed, config=config)

@app.route('/api/order', methods=['POST'])
def submit_order():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        client_name = request.form.get('client_name', 'Unknown')
        client_email = request.form.get('client_email', 'unknown@example.com')
        service = request.form.get('service')
        details = request.form.get('details')
        
        file_data = None
        file_name = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                import base64
                mimetype = file.mimetype
                base64_str = base64.b64encode(file.read()).decode('utf-8')
                file_data = f"data:{mimetype};base64,{base64_str}"
                file_name = secure_filename(file.filename)
    else:
        # Fallback for old json requests if any
        data = request.json or {}
        client_name = data.get('client_name', 'Unknown')
        client_email = data.get('client_email', 'unknown@example.com')
        service = data.get('service')
        details = data.get('details')
        file_data = None
        file_name = None
    
    if not service or not details:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
    inquiry_doc = {
        "client_name": client_name,
        "client_email": client_email,
        "service": service, 
        "details": details, 
        "timestamp": datetime.now(), 
        "status": "New",
        "history": []
    }
    
    if file_data and file_name:
        inquiry_doc['file_data'] = file_data
        inquiry_doc['file_name'] = file_name
        
    result = db.inquiries.insert_one(inquiry_doc)
    inquiry_id = str(result.inserted_id)
    
    db.notifications.insert_one({"type": "NEW INQUIRY", "message": f"#{inquiry_id} - {service}", "timestamp": datetime.now(), "is_read": 0})
    
    send_email_notification(inquiry_id, service, details)
    sync_to_spreadsheet(inquiry_id, service, details)
    
    return jsonify({"status": "success", "message": "Order submitted successfully! We will contact you soon."})

@app.route('/api/inquiry/<inquiry_id>', methods=['GET', 'DELETE'])
def handle_inquiry(inquiry_id):
    try:
        obj_id = ObjectId(inquiry_id)
    except:
        return jsonify({"status": "error", "message": "Invalid inquiry ID"}), 400
        
    if request.method == 'DELETE':
        result = db.inquiries.delete_one({"_id": obj_id})
        if result.deleted_count > 0:
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Inquiry not found"}), 404
        
    # GET method
    inquiry = db.inquiries.find_one({"_id": obj_id})
    if inquiry:
        inquiry['_id'] = str(inquiry['_id'])
        inquiry['history'] = inquiry.get('history', [])
        return jsonify({"status": "success", "inquiry": inquiry})
    return jsonify({"status": "error", "message": "Inquiry not found"}), 404

@app.route('/api/vendor-inquiry', methods=['POST'])
def submit_vendor_inquiry():
    data = request.json
    mobile = data.get('mobile')
    email = data.get('email')
    city = data.get('city')
    category = data.get('category')
    
    if not mobile or not email or not city or not category:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
        
    db.vendor_inquiries.insert_one({
        "mobile": mobile, 
        "email": email,
        "city": city, 
        "category": category, 
        "timestamp": datetime.now(), 
        "status": "New"
    })
    
    db.notifications.insert_one({"type": "NEW VENDOR", "message": f"{category} in {city}", "timestamp": datetime.now(), "is_read": 0})
    
    return jsonify({"status": "success", "message": "Details submitted successfully!"})

def send_email_smtp(receiver_email, message_body, subject="Chhatrapati Digital"):
    sender_email = "agent4@indusschool.com"
    sender_password = "Agent@2026"
    

    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Reply-To'] = "raochethan604@gmail.com"
    msg['Subject'] = subject
    msg.attach(MIMEText(message_body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.office365.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send vendor email: {e}")
        return False

@app.route('/api/vendor-inquiry/<vendor_id>/email', methods=['POST'])
def send_vendor_email(vendor_id):
    data = request.json
    message = data.get('message')
    
    if not message:
        return jsonify({"status": "error", "message": "Message is required"}), 400
        
    try:
        vendor_obj_id = ObjectId(vendor_id)
    except:
        return jsonify({"status": "error", "message": "Invalid vendor ID"}), 400
        
    vendor = db.vendor_inquiries.find_one({"_id": vendor_obj_id})
    if vendor:
        receiver_email = vendor.get('email')
        
        # Send real email
        success = send_email_smtp(receiver_email, message, subject="Chhatrapati Digital - Vendor Inquiry Reply")
        
        # Also log to outbox as a backup/record (wrapped in try/except for Vercel read-only FS)
        try:
            with open('email_outbox.txt', 'a') as f:
                f.write(f"--- EMAIL TO VENDOR {'[SENT]' if success else '[FAILED]'} ---\n")
                f.write(f"To: {receiver_email}\n")
                f.write(f"Subject: Chhatrapati Digital - Vendor Inquiry Reply\n")
                f.write(f"Message: {message}\n")
                f.write("-------------------------------\n\n")
        except Exception as fs_err:
            print("Could not write to email_outbox.txt (likely Vercel read-only filesystem):", fs_err)
            
        if success:
            db.vendor_inquiries.update_one(
                {"_id": vendor_obj_id}, 
                {
                    "$set": {"status": "Contacted"},
                    "$push": {"history": {"message": message, "timestamp": datetime.now()}}
                }
            )
            db.notifications.insert_one({"type": "EMAIL SENT", "message": f"To vendor: {receiver_email}", "timestamp": datetime.now(), "is_read": 0})
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "SMTP failed to send email. Check server logs."}), 500
            
    return jsonify({"status": "error", "message": "Vendor not found"}), 404

@app.route('/api/vendor-inquiry/<vendor_id>', methods=['DELETE'])
def delete_vendor_inquiry(vendor_id):
    result = db.vendor_inquiries.delete_one({"_id": ObjectId(vendor_id)})
    if result.deleted_count > 0:
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Vendor not found"}), 404

@app.route('/admin/inquiries')
def admin_inquiries():
    inquiries = convert_ids(db.inquiries.find().sort("timestamp", -1))
    vendor_inquiries = convert_ids(db.vendor_inquiries.find().sort("timestamp", -1))
    profile = convert_id(db.admin_profile.find_one())
    reviews = convert_ids(db.reviews.find().sort("timestamp", -1))
    
    pricing = convert_ids(db.pricing_packages.find())
    services = convert_ids(db.services.find())
    portfolio = convert_ids(db.portfolio.find())
    story = convert_id(db.our_story.find_one())
    config = convert_id(db.site_config.find_one())
    if not config:
        config = {
            "hero_title": "Transform Your Brand with<br>High-End Digital Solutions",
            "hero_subtitle": "We create stunning designs, professional photography, and premium signage that drive sales and build trust.",
            "contact_email": "raochethan604@gmail.com",
            "contact_phone": "+91 74830 06958",
            "whatsapp_num": "917483006958",
            "instagram_link": "https://www.instagram.com/mr_drackey02?igsh=dW02NmNiYmttdDBi",
            "facebook_link": "#",
            "linkedin_link": "#"
        }
    
    if story:
        stats_raw = story['stats'].split(',')
        stats_list = [{'val': s.split('|')[0], 'label': s.split('|')[1]} for s in stats_raw if '|' in s]
        story = dict(story)
        story['stats_list'] = stats_list
    cms_data = {
        'pricing': pricing,
        'services': services,
        'portfolio': portfolio,
        'story': story,
        'config': config
    }
    
    invoices = convert_ids(db.invoices.find().sort("timestamp", -1))
    tickets = convert_ids(db.client_tickets.find().sort("timestamp", -1))
    
    total_inquiries = len(inquiries)
    pending_review = sum(1 for i in inquiries if i.get('status', 'New') in ('New', 'Pending'))
    active_projects = sum(1 for i in inquiries if i.get('status') == 'Active Project')
    completed_projects = sum(1 for i in inquiries if i.get('status') == 'Completed')
    
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
        "unresolved_tickets": sum(1 for t in tickets if t.get('status') != 'Resolved')
    }
    
    return render_template('admin_dashboard.html', inquiries=inquiries, vendor_inquiries=vendor_inquiries, reviews=reviews, metrics=metrics, profile=profile, cms=cms_data, invoices=invoices, tickets=tickets)

@app.route('/api/profile', methods=['GET', 'POST'])
def handle_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bio = request.form.get('bio')
        
        avatar_data_uri = None
        if 'avatar_file' in request.files:
            file = request.files['avatar_file']
            if file and file.filename != '':
                import base64
                mimetype = file.mimetype
                base64_str = base64.b64encode(file.read()).decode('utf-8')
                avatar_data_uri = f"data:{mimetype};base64,{base64_str}"
                
        update_data = {"name": name, "email": email, "phone": phone, "bio": bio}
        if avatar_data_uri:
            update_data["avatar"] = avatar_data_uri
            
        profile = db.admin_profile.find_one()
        if profile:
            db.admin_profile.update_one({"_id": profile["_id"]}, {"$set": update_data})
            
        return jsonify({"status": "success", "avatar": avatar_data_uri})
        
    profile = convert_id(db.admin_profile.find_one())
    return jsonify({"status": "success", "profile": profile})

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    notifications = convert_ids(db.notifications.find().sort("timestamp", -1).limit(5))
    return jsonify({"status": "success", "notifications": notifications})

@app.route('/api/inquiries/<inquiry_id>/status', methods=['POST'])
def update_inquiry_status(inquiry_id):
    data = request.json
    new_status = data.get('status')
    
    db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {"$set": {"status": new_status}})
    
    email_dispatched = False
    if new_status == 'Active Project':
        db.notifications.insert_one({"type": "AUTOMATED EMAIL", "message": f"Welcome packet sent for #{inquiry_id}", "timestamp": datetime.now(), "is_read": 0})
        email_dispatched = True
        
        with open('email_outbox.txt', 'a') as f:
            f.write(f"--- AUTOMATED WELCOME EMAIL ---\n")
            f.write(f"To: Inquiry #{inquiry_id}\n")
            f.write(f"Subject: Welcome to Chhatrapati Digital - Next Steps\n")
            f.write(f"Body: Hello! We are thrilled to start working on your project. Here is your welcome packet and timeline...\n")
            f.write("-------------------------------\n\n")
            
    return jsonify({"status": "success", "email_dispatched": email_dispatched})

@app.route('/api/inquiries/<inquiry_id>/action', methods=['POST'])
def execute_inquiry_action(inquiry_id):
    data = request.json
    action_type = data.get('action_type')
    details = data.get('details')
    
    inquiry = db.inquiries.find_one({"_id": ObjectId(inquiry_id)})
    if not inquiry:
        return jsonify({"status": "error", "message": "Inquiry not found"}), 404
        
    receiver_email = inquiry.get('client_email', 'unknown@example.com')
    
    if action_type == 'quote':
        cost = details.get('cost', '0')
        time = details.get('time', 'TBD')
        desc = details.get('desc', 'Standard service')
        email_message = f"Hello {inquiry.get('client_name', 'Client')},\n\nWe have reviewed your request for {inquiry.get('service')}. Based on your details, here is our quotation:\n\nEstimated Cost: ₹{cost}\nEstimated Timeline: {time} days\nDeliverables: {desc}\n\nPlease let us know if you would like to proceed.\n\nBest,\nChhatrapati Digital"
        
        success = send_email_smtp(receiver_email, email_message, subject=f"Chhatrapati Digital - Quotation for {inquiry.get('service')}")
        
        db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {
            "$set": {"status": 'Quoted'},
            "$push": {"history": {"message": f"Quotation Sent (₹{cost}, {time} days):\n{desc}", "timestamp": datetime.now()}}
        })
        db.notifications.insert_one({"type": "QUOTE SENT", "message": f"#{inquiry_id} - ₹{cost}", "timestamp": datetime.now(), "is_read": 0})
        
    elif action_type == 'email':
        email_message = details.get('message', '')
        success = send_email_smtp(receiver_email, email_message, subject=f"Chhatrapati Digital - Re: {inquiry.get('service')} Project")
        
        db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {
            "$set": {"status": 'Contacted'},
            "$push": {"history": {"message": email_message, "timestamp": datetime.now()}}
        })
        db.notifications.insert_one({"type": "EMAIL SENT", "message": f"#{inquiry_id} to {receiver_email}", "timestamp": datetime.now(), "is_read": 0})
        
    elif action_type == 'consultation':
        email_message = f"Hello {inquiry.get('client_name', 'Client')},\n\nWe would love to schedule a consultation call to discuss your {inquiry.get('service')} project in detail. Please reply to this email with a few times that work for you.\n\nBest,\nChhatrapati Digital"
        success = send_email_smtp(receiver_email, email_message, subject=f"Chhatrapati Digital - Consultation for {inquiry.get('service')}")
        
        db.inquiries.update_one({"_id": ObjectId(inquiry_id)}, {
            "$set": {"status": 'Contacted'},
            "$push": {"history": {"message": "Consultation request sent.", "timestamp": datetime.now()}}
        })
        db.notifications.insert_one({"type": "CONSULTATION", "message": f"#{inquiry_id} to {receiver_email}", "timestamp": datetime.now(), "is_read": 0})
        
    if not success:
        return jsonify({"status": "error", "message": "Failed to dispatch email via SMTP."}), 500
        
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
                
        result = db.reviews.insert_one({
            "client_name": client_name,
            "rating": rating,
            "review_text": review_text,
            "video_path": video_path,
            "status": "Pending",
            "timestamp": datetime.now()
        })
        
        db.notifications.insert_one({"type": "NEW REVIEW", "message": f"By {client_name} - {rating} Stars", "timestamp": datetime.now(), "is_read": 0})
        return render_template('leave_review.html', success=True)
        
    return render_template('leave_review.html')

@app.route('/api/reviews/<review_id>/status', methods=['POST'])
def update_review_status(review_id):
    data = request.json
    new_status = data.get('status')
    db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": {"status": new_status}})
    return jsonify({"status": "success"})

@app.route('/api/cms/config', methods=['POST'])
def update_config():
    data = request.json
    config = db.site_config.find_one()
    if config:
        db.site_config.update_one({"_id": config["_id"]}, {"$set": {
            "hero_title": data.get('hero_title'),
            "hero_subtitle": data.get('hero_subtitle'),
            "contact_email": data.get('contact_email'),
            "contact_phone": data.get('contact_phone'),
            "whatsapp_num": data.get('whatsapp_num'),
            "instagram_link": data.get('instagram_link'),
            "facebook_link": data.get('facebook_link'),
            "linkedin_link": data.get('linkedin_link')
        }})
    else:
        db.site_config.insert_one(data)
    return jsonify({"status": "success"})

@app.route('/api/cms/pricing', methods=['POST'])
def update_pricing():
    data = request.json
    for item in data.get('packages', []):
        db.pricing_packages.update_one({"_id": ObjectId(item['id'])}, {"$set": {
            "name": item['name'],
            "price": item['price'],
            "features": item['features'],
            "is_popular": item['is_popular']
        }})
    return jsonify({"status": "success"})

@app.route('/api/cms/services', methods=['POST'])
def update_services():
    data = request.json
    for item in data.get('services', []):
        db.services.update_one({"_id": ObjectId(item['id'])}, {"$set": {
            "icon": item['icon'],
            "title": item['title'],
            "description": item['description']
        }})
    return jsonify({"status": "success"})

@app.route('/api/cms/story', methods=['POST'])
def update_story():
    data = request.json
    story = db.our_story.find_one()
    if story:
        db.our_story.update_one({"_id": story["_id"]}, {"$set": {
            "headline": data['headline'],
            "paragraph": data['paragraph'],
            "stats": data['stats']
        }})
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
        db.portfolio.insert_one({
            "project_name": project_name,
            "category": category,
            "image_url": image_url,
            "work_process": work_process
        })
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "No image uploaded"})

@app.route('/api/cms/portfolio/<item_id>', methods=['DELETE'])
def delete_portfolio(item_id):
    db.portfolio.delete_one({"_id": ObjectId(item_id)})
    return jsonify({"status": "success"})

@app.route('/api/invoices', methods=['POST'])
def save_invoice():
    data = request.json
    db.invoices.insert_one({
        "client_name": data.get('client_name'),
        "po_num": data.get('po_num'),
        "total": data.get('total'),
        "timestamp": datetime.now()
    })
    return jsonify({"status": "success"})

@app.route('/pay/<po_num>')
def pay_invoice(po_num):
    invoice = convert_id(db.invoices.find_one({"po_num": po_num}, sort=[("timestamp", -1)]))
    if not invoice:
        if po_num == '#CD-1001':
            invoice = {'po_num': '#CD-1001', 'client_name': 'Mock Client', 'total': 4999.00, 'timestamp': '2026-06-15'}
        else:
            return "Invoice not found.", 404
    return render_template('payment.html', invoice=invoice)

@app.route('/print/<po_num>')
def print_invoice(po_num):
    invoice = convert_id(db.invoices.find_one({"po_num": po_num}, sort=[("timestamp", -1)]))
    if not invoice:
        if po_num == '#CD-1001':
            invoice = {'po_num': '#CD-1001', 'client_name': 'Mock Client', 'total': 4999.00, 'timestamp': '2026-06-15'}
        else:
            return "Invoice not found.", 404
    
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
                <div><strong>Date:</strong> {str(invoice['timestamp']).split(' ')[0]}</div>
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

@app.route('/api/invoices/<invoice_id>', methods=['DELETE'])
def delete_invoice(invoice_id):
    db.invoices.delete_one({"_id": ObjectId(invoice_id)})
    return jsonify({"status": "success"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return jsonify({"status": "success", "redirect": "/dashboard"})
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        return jsonify({"status": "success", "redirect": "/admin/inquiries"})
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    invoices = convert_ids(db.invoices.find().sort("_id", -1))
    tickets = convert_ids(db.client_tickets.find().sort("_id", -1))
    inquiries = convert_ids(db.inquiries.find().sort("timestamp", -1))
    
    return render_template('dashboard.html', invoices=invoices, tickets=tickets, inquiries=inquiries)

@app.route('/api/client/tickets', methods=['POST'])
def add_client_ticket():
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    db.client_tickets.insert_one({
        "email": email,
        "subject": subject,
        "message": message,
        "status": "Open",
        "timestamp": datetime.now()
    })
    db.notifications.insert_one({"type": "SUPPORT TICKET", "message": f"New ticket: {subject}", "timestamp": datetime.now(), "is_read": 0})
    return jsonify({"status": "success"})

@app.route('/api/admin/tickets/<ticket_id>/resolve', methods=['POST'])
def resolve_client_ticket(ticket_id):
    ticket = db.client_tickets.find_one({"_id": ObjectId(ticket_id)})
    if ticket:
        db.client_tickets.update_one(
            {"_id": ObjectId(ticket_id)}, 
            {"$set": {"status": "Resolved", "resolved_at": datetime.now()}}
        )
        client_email = ticket.get('email')
        if client_email:
            subject_text = ticket.get('subject', 'Your Support Ticket')
            email_message = f"Hello,\n\nWe are writing to let you know that your support ticket regarding '{subject_text}' has been marked as Resolved.\n\nThank you for reaching out to us.\n\nBest,\nChhatrapati Digital Support"
            send_email_smtp(client_email, email_message, subject=f"Resolved: {subject_text}")
    return jsonify({"status": "success"})

@app.route('/api/admin/reviews', methods=['POST'])
def add_review():
    client_name = request.form.get('client_name')
    rating = int(request.form.get('rating', 5))
    review_text = request.form.get('review_text')
    
    video_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            import base64
            mimetype = file.mimetype
            base64_str = base64.b64encode(file.read()).decode('utf-8')
            video_path = f"data:{mimetype};base64,{base64_str}"
            
    db.reviews.insert_one({
        "client_name": client_name,
        "rating": rating,
        "review_text": review_text,
        "video_path": video_path,
        "status": "Approved",
        "timestamp": datetime.now()
    })
    return jsonify({"status": "success"})

@app.route('/api/admin/reviews/<review_id>', methods=['PUT'])
def edit_review(review_id):
    client_name = request.form.get('client_name')
    rating = int(request.form.get('rating', 5))
    review_text = request.form.get('review_text')
    
    update_data = {
        "client_name": client_name,
        "rating": rating,
        "review_text": review_text
    }
    
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename != '':
            import base64
            mimetype = file.mimetype
            base64_str = base64.b64encode(file.read()).decode('utf-8')
            update_data["video_path"] = f"data:{mimetype};base64,{base64_str}"
            
    db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": update_data})
    return jsonify({"status": "success"})

@app.route('/api/admin/reviews/<review_id>', methods=['DELETE'])
def delete_review_endpoint(review_id):
    db.reviews.delete_one({"_id": ObjectId(review_id)})
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
