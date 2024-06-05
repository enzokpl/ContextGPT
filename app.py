import streamlit as st
import requests
import json

# Título da aplicação
st.title('Chatbot com Contexto de Projeto')

# API endpoint (substitua com o seu endpoint real)
API_ENDPOINT = 'http://127.0.0.1:5000/generate-response'

# Barra lateral para exibir contexto relevante (opcional)
st.sidebar.header('Contexto Relevante (opcional)')

# Armazenar o histórico da conversa
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Exibir o histórico da conversa
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Caixa de entrada de texto para o usuário
if prompt := st.chat_input("Digite sua pergunta"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Enviar a pergunta para a API e obter a resposta
    payload = {"prompt": prompt}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(API_ENDPOINT, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        response_text = response_data.get('response', 'Desculpe, não entendi.')
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Exibir a resposta na interface
        with st.chat_message("assistant"):
            st.markdown(response_text)
    else:
        st.error('Erro na API:', response.status_code)