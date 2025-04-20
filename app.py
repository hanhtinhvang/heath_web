from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from PyPDF2 import PdfReader

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# At the top after imports
import logging
logging.basicConfig(level=logging.DEBUG)

# Update the admin_login route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    app.logger.debug(f"Templates folder: {app.template_folder}")
    app.logger.debug(f"Current directory: {os.getcwd()}")
    app.logger.debug("Accessing admin login route")
    try:
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            app.logger.debug(f"Login attempt - username: {username}")
            
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session['admin'] = True
                return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html')
    except Exception as e:
        app.logger.error(f"Error in admin_login: {str(e)}")
        return str(e), 500

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    try:
        with open('chat_history.json', 'r') as f:
            chat_history = json.load(f)
    except:
        chat_history = []
    
    return render_template('admin_dashboard.html', chat_history=chat_history)

# Add to imports
from PyPDF2 import PdfReader

# Add this function after allowed_file function
def extract_pdf_content(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF content: {str(e)}")
        return ""

# Modify upload_file function to process PDF after upload
@app.route('/admin/upload', methods=['POST'])
def upload_file():
    if not session.get('admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        if filename.lower().endswith('.pdf'):
            content = extract_pdf_content(file_path)
            # Save extracted content to a text file
            with open(os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.txt"), 'w', encoding='utf-8') as f:
                f.write(content)
        
        return jsonify({'success': True, 'filename': filename})
    
    return jsonify({'error': 'File type not allowed'})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    response = get_response("", user_message)
    save_chat_history(user_message, response)
    return jsonify({'response': response})

def get_response(context, user_input):
    try:
        question = user_input.lower()
        
        if 'đau đầu' in question or 'nhức đầu' in question:
            return "Nguyên nhân phổ biến gây đau đầu bao gồm căng thẳng, mất nước, thiếu ngủ hoặc mỏi mắt. Để giảm đau:\n" + \
                   "1. Nghỉ ngơi trong phòng yên tĩnh, tối\n" + \
                   "2. Uống đủ nước\n" + \
                   "3. Dùng thuốc giảm đau không kê đơn\n" + \
                   "Hãy đến gặp bác sĩ nếu đau đầu dữ dội hoặc thường xuyên."
                   
        elif 'sốt' in question:
            return "Cách xử lý khi bị sốt:\n" + \
                   "1. Nghỉ ngơi và uống nhiều nước\n" + \
                   "2. Dùng thuốc hạ sốt\n" + \
                   "3. Chườm mát\n" + \
                   "Cần đến bệnh viện nếu sốt trên 39.4°C hoặc kéo dài hơn 3 ngày."
                   
        elif 'cảm' in question or 'cúm' in question:
            return "Điều trị cảm cúm:\n" + \
                   "1. Nghỉ ngơi đầy đủ\n" + \
                   "2. Uống nhiều nước\n" + \
                   "3. Dùng thuốc cảm thông thường\n" + \
                   "4. Dùng mật ong khi đau họng\n" + \
                   "Gặp bác sĩ nếu triệu chứng nặng hơn hoặc kéo dài hơn một tuần."
                   
        else:
            return "Tôi có thể cung cấp thông tin về các vấn đề sức khỏe thông thường. Hãy hỏi cụ thể về triệu chứng của bạn."

    except Exception as e:
        return f"Đã xảy ra lỗi: {str(e)}"

# Add this function after your imports
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the upload folder path to be absolute
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Add this after app configuration
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Add after get_response function
def save_chat_history(user_message, bot_response):
    try:
        chat_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_message': user_message,
            'bot_response': bot_response
        }
        
        try:
            with open('chat_history.json', 'r') as f:
                chat_history = json.load(f)
        except:
            chat_history = []
            
        chat_history.append(chat_entry)
        
        with open('chat_history.json', 'w') as f:
            json.dump(chat_history, f, indent=4)
    except Exception as e:
        print(f"Error saving chat history: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)