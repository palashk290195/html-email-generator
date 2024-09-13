import os
from flask import Flask, render_template, request, jsonify, session, url_for, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from flask_session import Session
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
Session(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', 
                           system_prompt=session.get('system_prompt', ''),
                           api_key=session.get('api_key', ''),
                           receiver_profile_details=session.get('receiver_profile_details', ''),
                           sender_profile_details=session.get('sender_profile_details', ''),
                           purpose=session.get('purpose',''),
                           chat_history=[msg for msg in session.get('chat_history', []) if msg['role'] == 'user'],
                           logo=session.get('logo', 'default_logo.png'))

@app.route('/upload_logo', methods=['POST'])
def upload_logo():
    if 'logo' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    file = request.files['logo']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        session['logo'] = filename
        return jsonify({"success": True, "filename": filename})
    return jsonify({"success": False, "error": "Invalid file type"}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_chat', methods=['POST'])
def update_chat():
    try:
        data = request.form
        session['system_prompt'] = data.get('system_prompt', '')
        session['api_key'] = data.get('api_key', '').strip()
        session['receiver_profile_details'] = data.get('receiver_profile_details', '')
        session['sender_profile_details'] = data.get('sender_profile_details', '')
        session['purpose'] = data.get('purpose', '')
        user_message = data.get('user_message', '')
        logo_url = data.get('logo_url', '')

        if not session['api_key']:
            raise ValueError("API key is missing or empty")

        if 'chat_history' not in session:
            session['chat_history'] = []

        chat_history = session['chat_history']
        
        client = OpenAI(api_key=session['api_key'])
        
        messages = [
            {"role": "system", "content": session['system_prompt']},
            {"role": "user", "content": f"Receiver Profile details: {session['receiver_profile_details']} \n Sender Profile details: {session['sender_profile_details']} \n Purpose: {session['purpose']} \n Logo URL: {logo_url}"},
        ]
        
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        ai_response = response.choices[0].message.content

        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": ai_response})
        session['chat_history'] = chat_history

        return jsonify({"success": True, "response": ai_response})
    except Exception as e:
        app.logger.error(f"Error in update_chat: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    session['chat_history'] = []
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)