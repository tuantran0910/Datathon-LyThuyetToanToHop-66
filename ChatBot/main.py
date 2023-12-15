import os
import json
import base64
import flask_login
import openai
import requests
from .classes import Suggestion
from dotenv.main import load_dotenv
from flask import Blueprint, Flask, jsonify, render_template, request, send_from_directory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

# Langchain settings
# list(map(asdict, suggestion)) # change to dictionary
suggestion_list = [
    Suggestion('OP1', 'hi'),
    Suggestion('OP2', 'helo')
]
llm = OpenAI(model="text-davinci-003")
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)

# Blueprint
main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('base.html')

# @main.route('/print')
# def print_image(img_urls):
#     for img_url in img_urls:
#         # Return json file

#     # Save to static cloth folder and rename xxxxx.jpg

# Aanh -> server upload
# client : req = anh -> server rec : function upload


@main.route('/upload', methods=['POST'])
def upload_image():
    try:
        file = request.files['fileInput']
    except Exception as e:
        return jsonify({"message": str(e), "response": False})

    # Move the file to the 'static' folder
    file.save(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'static', file.filename))
    # Add userid to the file name
    return jsonify({"message": "Upload success", "response": True})


@main.route('/getcloth', methods=['POST'])
def get_cloth():
    try:
        urls = json.loads(request.form['urls'])
        print(urls)
    except Exception as e:
        return jsonify({"message": str(e), "response": False})
    imgs = []
    for url in urls:
        with open(url, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            imgs.append(base64_data)
    return jsonify({"imgs": imgs, "response": True})


def get_random_image(num=3):
    # Get the relative path of 3 random images in static folder
    static_folder = os.path.join(os.path.dirname(
        os.path.relpath(__file__)), 'static')
    img_list = []

    for filename in os.listdir(static_folder):
        if len(img_list) == num:
            break

        if filename.endswith('.jpg'):
            img_list.append(os.path.join(os.path.dirname(
                os.path.relpath(__file__)), 'static', filename))
    # Return a list of relative path
    return img_list


@main.route('/data', methods=['POST'])
def get_data():
    data = request.get_json()
    text = data.get('data')
    user_input = text

    if user_input.strip().lower() == "random anh":
        imgs = get_random_image()
        print(imgs)
        return jsonify({"message": imgs, "list": True, "response": True})

    try:
        conversation = ConversationChain(llm=llm, memory=memory)
        output = conversation.predict(input=user_input)
        memory.save_context({"input": user_input}, {"output": output})
        return jsonify({"response": True, "list": False, "message": output})
    except Exception as e:
        print(e)
        error_message = f'Error: {str(e)}'
        return jsonify({"message": error_message, "list": False, "response": False})


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


def clear_static_folder():
    static_folder = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), 'static')
    for filename in os.listdir(static_folder):
        if filename.endswith('.jpg'):
            file_path = os.path.join(static_folder, filename)
            os.remove(file_path)


@flask_login.login_required
def test():
    user = flask_login.current_user
    user_name = user.name
