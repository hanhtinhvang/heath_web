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
# Add this variable at the top with other globals
pdf_content_cache = {}

# Update the upload_file function to cache PDF content
@app.route('/admin/upload', methods=['POST'])
def upload_file():
    app.logger.debug("Starting file upload...")
    if not session.get('admin'):
        app.logger.debug("Unauthorized upload attempt")
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'file' not in request.files:
        app.logger.debug("No file part in request")
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    app.logger.debug(f"Received file: {file.filename}")
    
    if file.filename == '':
        app.logger.debug("No selected file")
        return jsonify({'error': 'No selected file'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        app.logger.debug(f"Saving file to: {file_path}")
        file.save(file_path)
        
        if filename.lower().endswith('.pdf'):
            app.logger.debug("Processing PDF file...")
            content = extract_pdf_content(file_path)
            pdf_content_cache[filename] = content
            text_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}.txt")
            app.logger.debug(f"Saving extracted text to: {text_path}")
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        app.logger.debug("File upload completed successfully")
        return jsonify({'success': True, 'filename': filename})
    
    app.logger.debug("File type not allowed")
    return jsonify({'error': 'File type not allowed'})

# Update get_response function
def get_response(context, user_input):
    try:
        question = user_input.lower()
        
        # Check for Thông tư 50 related questions
        if 'thông tư 50' in question or 'tt50' in question or 'tt 50' in question:
            # Search through cached PDF content
            for filename, content in pdf_content_cache.items():
                if '50' in filename and content:
                    # Extract relevant sections based on the question
                    if 'mục đích' in question or 'nội dung' in question:
                        return f"Theo Thông tư 50:\n{content[:1000]}..."
                    elif 'phạm vi' in question:
                        return f"Phạm vi áp dụng của Thông tư 50:\n{content[1000:2000]}..."
                    else:
                        return f"Thông tư số 50 quy định về:\n{content[:500]}...\n\nBạn muốn biết thêm về phần nào? (Ví dụ: mục đích, phạm vi áp dụng)"
            
            return "Tôi đã được cập nhật về Thông tư 50, vui lòng hỏi cụ thể về phần bạn muốn tìm hiểu."
        
        # Existing conditions remain unchanged
        if 'đau đầu' in question:
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