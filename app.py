from flask import Flask, render_template, request, jsonify
import hashlib
import os
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Common password dictionary (for demo purposes)
COMMON_PASSWORDS = [
    "123456", "password", "123456789", "12345", "12345678",
    "qwerty", "abc123", "password123", "admin", "letmein",
    "welcome", "monkey", "dragon", "baseball", "football",
    "master", "superman", "iloveyou", "trustno1", "shadow",
    "sunshine", "princess", "pokemon", "computer", "whatever"
]

def calculate_hashes(password):
    """Calculate various hash types for a given password"""
    return {
        'md5': hashlib.md5(password.encode()).hexdigest(),
        'sha1': hashlib.sha1(password.encode()).hexdigest(),
        'sha256': hashlib.sha256(password.encode()).hexdigest(),
        'sha512': hashlib.sha512(password.encode()).hexdigest()
    }

def crack_password_thread(target_hash, hash_type, result_dict, index):
    """Thread function to crack password"""
    for password in COMMON_PASSWORDS:
        calculated_hash = calculate_hashes(password)[hash_type]
        if calculated_hash == target_hash:
            result_dict[index] = {
                'found': True,
                'password': password,
                'hash_type': hash_type,
                'hash': target_hash
            }
            return
        time.sleep(0.1)  # Simulate cracking time
    
    result_dict[index] = {'found': False}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
        
        # Try to parse the content as a hash
        hash_value = content
        
        # Determine hash type by length
        hash_types = {
            32: 'md5',
            40: 'sha1',
            64: 'sha256',
            128: 'sha512'
        }
        
        hash_type = hash_types.get(len(hash_value), 'unknown')
        
        return jsonify({
            'success': True,
            'hash': hash_value,
            'hash_type': hash_type,
            'message': f'File uploaded successfully. Detected hash type: {hash_type}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/crack', methods=['POST'])
def crack():
    data = request.json
    target_hash = data.get('hash')
    hash_type = data.get('hash_type')
    
    if hash_type == 'unknown':
        return jsonify({'error': 'Unknown hash type'}), 400
    
    # Multi-threaded cracking simulation
    results = {}
    threads = []
    
    # Create a thread for each hash type if not specified
    if hash_type == 'auto':
        hash_types_to_try = ['md5', 'sha1', 'sha256', 'sha512']
    else:
        hash_types_to_try = [hash_type]
    
    for i, ht in enumerate(hash_types_to_try):
        thread = threading.Thread(
            target=crack_password_thread,
            args=(target_hash, ht, results, i)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    for result in results.values():
        if result['found']:
            # Calculate all hashes for the found password
            all_hashes = calculate_hashes(result['password'])
            return jsonify({
                'success': True,
                'password': result['password'],
                'cracked_hash_type': result['hash_type'],
                'cracked_hash': result['hash'],
                'all_hashes': all_hashes,
                'message': f'Password cracked successfully!'
            })
    
    return jsonify({
        'success': False,
        'message': 'Password not found in common password list'
    })

@app.route('/hash', methods=['POST'])
def hash_password():
    data = request.json
    password = data.get('password')
    
    if not password:
        return jsonify({'error': 'No password provided'}), 400
    
    hashes = calculate_hashes(password)
    
    return jsonify({
        'success': True,
        'hashes': hashes
    })

if __name__ == '__main__':
    app.run(debug=True)