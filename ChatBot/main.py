import os
import json
import base64
import flask_login
import openai
import requests
import dotenv
import shutil
from io import BytesIO
from PIL import Image
from ..DM_VTON_new.verified_img import verified_input
from ..DM_VTON_new.main import tryon
from .classes import Suggestion
from .active_func import active_func
from .query_cloth import search_item
from dotenv.main import load_dotenv
from flask import Blueprint, Flask, jsonify, render_template, request, send_from_directory
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

dotenv.load_dotenv()

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


@main.route('/upload', methods=['POST'])
def upload_image():
    try:
        file = request.files['fileInput']
    except Exception as e:
        return jsonify({"message": str(e), "response": False})

    # Convert file to Image
    img = Image.open(file.stream)

    # Verify image
    if not verified_input(img):
        return jsonify({"message": """Upload unsuccessful! Thank you for choosing our service. We prioritize the highest level of privacy for your data. Unfortunately, your image is not approriate for the system. Please upload a photo with straight arms.""", "response": False})
    else:
        print("Accepted!")

    img.save(os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'static', 'pose', '000001_0.jpg'))
    # Add userid to the file name
    return jsonify({"message": "Upload successful! Thank you for choosing our service. We prioritize the highest level of privacy for your data.", "response": True})


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


@main.route('/data', methods=['POST'])
def get_data():
    data = request.get_json()
    text = data.get('data')
    user_input = text

    function_name, idx = active_func(user_input, memory)
    conversation = ConversationChain(llm=llm, memory=memory)
    print(function_name, idx)

    if function_name == "greeting":
        greeting_input = """
        You receive a greeting input. Please then say hello to user and make an introduction to the user about yourself and your functionailities as a shop assistant.
        """
        try:
            output = conversation.predict(input=greeting_input)
            memory.save_context({"input": greeting_input}, {"output": output})
            return jsonify({"response": True, "list": False, "message": output})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "refuseToAnswer":
        try:
            sorry_input = """
            You receive an input that is beyond the scope of your ability to answer. 
            Please then say sorry to user and make an announcement to the user to only ask about those information: 
            - 1. How to upload images.
            - 2. You can ask for cloth recommendation.
            - 3. You can request to try on a cloth item.
            """
            output = conversation.predict(input=sorry_input)
            memory.save_context({"input": sorry_input}, {"output": output})
            return jsonify({"response": True, "list": False, "message": output})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "uploadPose":
        upload_instructions = """Hello World"""
        try:
            instruction_input = """
            You have to provide instructions of how to upload photos based on the following format:
            {}
            """.format(upload_instructions)
            output = conversation.predict(input=instruction_input)
            memory.save_context(
                {"input": instruction_input}, {"output": output})
            return jsonify({"response": True, "list": False, "message": output})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "recommendCloth":
        # Remove all images in recommend_img folder
        recommend_img = os.path.join(os.path.dirname(os.path.realpath(
            __file__)), 'static', 'recommend_img')
        files = os.listdir(recommend_img)
        for file in files:
            file_path = os.path.join(recommend_img, file)
            if os.path.isfile(file_path) and file.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                os.remove(file_path)

        try:
            img_urls = search_item(user_input)[-1][1]

            if len(img_urls) == 0:
                return jsonify({"message": "Sorry, we cannot find any suitable clothes for you. Can you describe more details ?", "list": False, "response": True})

            data_folder = os.path.join(os.path.dirname(
                os.path.relpath(__file__)), 'data')
            recommend_img = os.path.join(os.path.dirname(os.path.realpath(
                __file__)), 'static', 'recommend_img')

            for i, img_url in enumerate(img_urls):
                destination_path = os.path.join(
                    recommend_img, f"00000{i + 1}_1.jpg")
                shutil.copy(data_folder + "/" + img_url, destination_path)

            img_urls_rel_path = [data_folder + "/" +
                                 img_url for img_url in img_urls]

            imgs = []
            for url in img_urls_rel_path:
                with open(url, 'rb') as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    imgs.append(base64_data)
            return jsonify({"message": "Here are some clothes that are suitable for your requirements.", "imgs": imgs, "list": True, "response": True})

        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "tryCloth":
        if not idx.isdigit():
            return jsonify({"message": "Please specify an approriate position for us.", "list": False, "response": True})
        else:
            idx = int(idx)

        # Create test_pairs.txt in folder static/try_on
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'try_on', 'test_pairs.txt'), 'w') as f:
            # Create a combination between pose and recommend_img idx image
            # Get the file name in pose folder
            pose_folder = os.path.join(os.path.dirname(os.path.realpath(
                __file__)), 'static', 'pose')
            pose_files = os.listdir(pose_folder)
            pose = pose_files[0]

            # Get the idx-th file name in recommend_img folder
            recommend_img_folder = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'static', 'recommend_img')
            recommend_img_files = os.listdir(recommend_img_folder)
            recommend_img = recommend_img_files.sort()
            recommend_img = recommend_img_files[idx - 1]

            # Write to test_pairs.txt
            f.write(pose + " " + recommend_img)

        try:
            
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

        return jsonify({"message": "Please upload your photo", "list": False, "response": True})

    # try:
    #     output = conversation.predict(input=user_input)
    #     memory.save_context({"input": user_input}, {"output": output})
    #     return jsonify({"response": True, "list": False, "message": output})
    # except Exception as e:
    #     print(e)
    #     error_message = f'Error: {str(e)}'
    #     return jsonify({"message": error_message, "list": False, "response": False})


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
