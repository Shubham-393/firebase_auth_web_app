from flask import Flask, render_template, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import datastore

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this in production

# Firebase Admin Initialization
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

# Google Cloud Datastore client
datastore_client = datastore.Client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify', methods=['POST'])
def verify():
    id_token = request.form['idToken']
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token['email']

        # Store user in Datastore if not already
        key = datastore_client.key('User', uid)
        user = datastore_client.get(key)
        if not user:
            entity = datastore.Entity(key)
            entity.update({
                'email': email,
                'uid': uid,
                'welcome_note': f"Hello {email}, this is your private dashboard!"
            })
            datastore_client.put(entity)

        session['user'] = email
        session['uid'] = uid
        return redirect(url_for('dashboard'))

    except Exception as e:
        return f"Token verification failed: {str(e)}", 400

@app.route('/dashboard')
def dashboard():
    if 'user' in session and 'uid' in session:
        key = datastore_client.key('User', session['uid'])
        user = datastore_client.get(key)
        return render_template('dashboard.html', user=session['user'], note=user['welcome_note'])
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
