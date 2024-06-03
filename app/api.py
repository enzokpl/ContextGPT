from flask import Flask, request, jsonify
import openai
from openai import OpenAI

from app.embeddings import get_embedding, find_most_relevant_embeddings
from .config import OPENAI_API_KEY
from flask_swagger_ui import get_swaggerui_blueprint
from flask import send_from_directory
from prometheus_flask_exporter import PrometheusMetrics

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# Configuração do Prometheus
metrics = PrometheusMetrics(app)

# Swagger UI configuration
SWAGGER_URL = '/swagger'
API_URL = '/swagger-static/openapi.yaml'  # Caminho para o arquivo YAML

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "ContextGPT API"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# Rota para servir arquivos estáticos, incluindo o openapi.yaml
@app.route('/swagger-static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# Dicionário para armazenar os embeddings dos arquivos
embeddings_context = {}
contents_context = {}


@app.route('/context', methods=['POST'])
def update_context():
    """
    Atualiza o contexto dos arquivos. Verifica se a entrada é JSON válida e atualiza o dicionário de contexto com o
    embedding e o conteúdo do arquivo fornecido.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid input, JSON expected."}), 400

    data = request.get_json(force=True)
    file_path = data.get('file_path')
    embedding = data.get('embedding')
    content = data.get('content')

    if file_path and embedding is not None and content is not None:
        embeddings_context[file_path] = embedding
        contents_context[file_path] = content
        return jsonify({"status": "success", "message": "Context updated."}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid data."}), 400


@app.route('/context/<path:file_path>', methods=['GET'])
def get_context(file_path):
    """
    Recupera o contexto de um arquivo específico.
    Retorna o conteúdo do arquivo armazenado no dicionário de contexto.
    """
    if file_path in embeddings_context:
        return jsonify({"status": "success", "content": embeddings_context[file_path]}), 200
    else:
        return jsonify({"status": "error", "message": "File not found."}), 404


@app.route('/context/<path:file_path>', methods=['DELETE'])
def delete_context(file_path):
    """
    Remove o contexto de um arquivo específico.
    """
    if file_path in embeddings_context:
        del embeddings_context[file_path]
        return jsonify({"status": "success", "message": "Context removed."}), 200
    else:
        return jsonify({"status": "error", "message": "File not found."}), 404


@app.route('/health', methods=['GET'])
def health_check():
    """
    Verifica o status de saúde da aplicação.
    """
    try:
        # Verifique se a API OpenAI está acessível
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Health check."},
                {"role": "user", "content": "Are you healthy?"}
            ],
            max_tokens=5)
        if response:
            return jsonify({"status": "success", "message": "Application is healthy."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Application is unhealthy: {str(e)}"}), 500


@app.route('/generate-response', methods=['POST'])
def generate_response():
    """
    Gera uma resposta usando o modelo GPT-4o da OpenAI. Adiciona o contexto relevante dos arquivos ao prompt
    fornecido pelo usuário e envia uma requisição para a API da OpenAI.
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid input, JSON expected."}), 400

    data = request.get_json(force=True)
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400

    query_embedding = get_embedding(prompt)
    relevant_files = find_most_relevant_embeddings(query_embedding, embeddings_context)

    # Adicionar contexto relevante dos arquivos ao prompt
    for file_path, _ in relevant_files:
        prompt += f"\n\nConteúdo do arquivo {file_path}:\n{contents_context[file_path]}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                 "content": "Você é um assistente que ajuda com explicações, implementações e erros de código "
                            "relacionados ao projeto que está observando."
                            "Você deve observar o contexto inteiro do projeto e providenciar respostas de acordo."
                            "Ao implementar código, deve realizar um passo-a-passo de como fazê-lo, apresentar "
                            "diretórios que deverão ser criados e fazer uma breve explicação de como testar se a "
                            "funcionalidade está operante."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500)
        return jsonify({"status": "success", "response": response.choices[0].message.content}), 200
    except openai.OpenAIError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
