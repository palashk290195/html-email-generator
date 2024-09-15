import os
from flask import Flask, render_template, request, jsonify, session, url_for, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from flask_session import Session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
import json
import colorgram
import tempfile

load_dotenv()

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
UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def search_unsplash(query):
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "page": 1,
        "per_page": 1,
        "client_id": UNSPLASH_ACCESS_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            first_image = data['results'][0]
            return {
                "url": first_image['urls']['regular'],
                "description": first_image['description'],
                "photographer": first_image['user']['name']
            }
    return None


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
        colors = "Not available"

        response = requests.get(logo_url, stream=True)
        if response.status_code == 200:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            # Step 2: Use colorgram to extract colors from the temporary file
            colors = colorgram.extract(temp_file_path, 2)
            print(colors)


            # Optional: You can delete the temporary file manually if needed
            os.remove(temp_file_path)
        else:
            print("Failed to download image")

        if not session['api_key']:
            raise ValueError("API key is missing or empty")

        if 'chat_history' not in session:
            session['chat_history'] = []

        chat_history = session['chat_history']
        
        client = OpenAI(api_key=session['api_key'])
        
        messages = [
            {"role": "system", "content": session['system_prompt']},
            {"role": "user", "content": f"Receiver Profile details: {session['receiver_profile_details']} \n Sender Profile details: {session['sender_profile_details']} \n Purpose: {session['purpose']} \n Logo URL: {logo_url} \n HTML color theme: {colors[1]}"},
        ]
        
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_unsplash",
                    "description": "Provide an image URL. Only call this function when there is a new requirement or replacement of image, don't call when image position needs to be changed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query for the image"
                            }
                        },
                        "required": ["query"],
                        "additionalPorperties": False
                    }
                }
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_name = message.tool_calls[0].function.name
            tool_args = eval(message.tool_calls[0].function.arguments)
            
            if tool_name == "search_unsplash":
                image_url = search_unsplash(tool_args['query'])
                # Create a message containing the result of the function call
                function_call_result_message = {
                    "role": "tool",
                    "content": json.dumps({
                        "query": tool_args['query'],
                        "image_url": image_url
                    }),
                    "tool_call_id": message.tool_calls[0].id
                }
                messages.append(message)
                messages.append(function_call_result_message)
                
                second_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages
                )
                ai_response = second_response.choices[0].message.content
        else:
            ai_response = message.content
        
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