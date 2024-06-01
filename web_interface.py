from flask import Flask, request, jsonify, render_template
import requests
import templates

app = Flask(__name__)

# URL da API Flask local
API_URL = "http://127.0.0.1:5000/generate-response"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['prompt']
    response = get_contextual_response(user_input)
    return jsonify({"response": response})

def get_contextual_response(prompt):
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['response']
    else:
        return f"Erro ao obter resposta da API. Status code: {response.status_code}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)
