# ContextGPT

ContextGPT é uma API Flask que utiliza o OpenAI GPT-4 para fornecer respostas contextuais baseadas no conteúdo dos arquivos monitorados em um diretório específico. A API é capaz de atualizar seu contexto em tempo real conforme os arquivos são modificados, criados ou excluídos.

## Funcionalidades

- Atualização em tempo real do contexto baseado em arquivos monitorados.
- Geração de respostas contextuais utilizando o modelo GPT-4 da OpenAI.
- Interface simples para integração com outros sistemas.

## Estrutura do Projeto

- `app/`: Contém a lógica principal da API e do monitoramento de arquivos.
  - `api.py`: Define as rotas da API Flask.
  - `monitor.py`: Implementa a lógica para monitorar arquivos e atualizar o contexto.
  - `config.py`: Contém a configuração da chave API da OpenAI.

## Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu_usuario/contextgpt.git
cd contextgpt
```

### 2. Criar e Ativar o Ambiente Virtual

```bash
python -m venv .venv
.venv\Scripts\activate  # No Windows
source .venv/bin/activate  # No Linux/Mac
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar a Chave API da OpenAI
Crie um arquivo config.py no diretório app com o seguinte conteúdo:

```
OPENAI_API_KEY = "sua_chave_api_openai"
```

### 5. Executar o Servidor Flask

```bash
python run.py
```

### 6. Iniciar o Monitoramento dos Arquivos

```bash
python -m app.monitor /caminho/para/seu/projeto
```