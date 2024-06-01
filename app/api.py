from flask import Flask, request, jsonify
import openai
from openai import OpenAI
from .config import OPENAI_API_KEY
client = OpenAI(api_key=OPENAI_API_KEY)


app = Flask(__name__)

# Dicionário para armazenar o contexto dos arquivos
context = {}


@app.route('/context', methods=['POST'])
def update_context():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid input, JSON expected."}), 400

    data = request.get_json(force=True)
    file_path = data.get('file_path')
    content = data.get('content')

    if file_path and content is not None:
        context[file_path] = content
        return jsonify({"status": "success", "message": "Context updated."}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid data."}), 400


@app.route('/context/<path:file_path>', methods=['GET'])
def get_context(file_path):
    if file_path in context:
        return jsonify({"status": "success", "content": context[file_path]}), 200
    else:
        return jsonify({"status": "error", "message": "File not found."}), 404


@app.route('/generate-response', methods=['POST'])
def generate_response():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid input, JSON expected."}), 400

    data = request.get_json(force=True)
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400

    # Adicionar contexto dos arquivos ao prompt
    for file_path, content in context.items():
        prompt += f"\n\nConteúdo do arquivo {file_path}:\n{content}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Você é um assistente que ajuda com explicações de código."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150)
        return jsonify({"status": "success", "response": response.choices[0].message.content}), 200
    except openai.OpenAIError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
