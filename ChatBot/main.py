import os
import flask_login
import openai
import requests
from .classes import Suggestion
from dotenv.main import load_dotenv
from flask import Blueprint, Flask, jsonify, render_template, request
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

# Langchain settings
# list(map(asdict, suggestion)) # change to dictionary
suggestion_list = [
    Suggestion('OP1', 'hi'),
    Suggestion('OP2', 'helo')
]
llm = OpenAI()
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)

# Blueprint
main = Blueprint('main', __name__)

# MAiN


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/upload', methods=['POST'])
def upload_image():
    try:
        file = request.files['fileInput']
    except Exception as e:
        return jsonify({"message": str(e), "response": False})

    # Move the file to the 'static' folder
    file.save(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'static', file.filename))
    return jsonify({"message": "Upload success", "response": True})


@main.route('/data', methods=['POST'])
def get_data():
    data = request.get_json()
    text = data.get('data')
    user_input = text
    try:
        conversation = ConversationChain(llm=llm, memory=memory)
        output = conversation.predict(input=user_input)
        memory.save_context({"input": user_input}, {"output": output})
        return jsonify({"response": True, "message": output})
    except Exception as e:
        print(e)
        error_message = f'Error: {str(e)}'
        return jsonify({"message": error_message, "response": False})


@main.route("/chatbot")
@flask_login.login_required
def chatbot():
    # generate appmassage
    # improve : data class -> dictionaries
    # suggestion_list = [
    #     {
    #         "Title" : "OP 1",
    #         "Message" : "1 + 1 bang bao nhieu"
    #     },
    #     {
    #         "Title" : "OP 2",
    #         "Message" : "2 + 1 bang bao nhieu"
    #     }
    # ] # content
    return render_template("chatbot.html", suggestion_list=suggestion_list)


@main.route('/profile')
@flask_login.login_required
def profile():
    user = flask_login.current_user
    return render_template('profile.html', user=user)
