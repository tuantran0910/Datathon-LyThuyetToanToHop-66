import os
import json
import base64
import flask_login
import openai
import requests
import dotenv
import shutil
import random
from io import BytesIO
from PIL import Image
from ..DM_VTON_new.verified_img import verified_input
from ..DM_VTON_new.main import tryon
from .classes import Suggestion
from .active_func import active_func
from .query_cloth import search_item
from .get_info import full_info
from .return_size_cloth import predict_new_data
from dotenv.main import load_dotenv
from flask import Blueprint, Flask, jsonify, render_template, request, send_from_directory, redirect, url_for
from langchain.chains import ConversationChain
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.output_parsers import CommaSeparatedListOutputParser
from langchain.prompts import PromptTemplate
dotenv.load_dotenv()


llm = OpenAI(model="text-davinci-003")
memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100)

# Blueprint
main = Blueprint('main', __name__)


@main.route('/')
def index():
    # return render_template('base.html')
    return redirect('/chatbot')


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
        You receive a greeting input. Your name is Cloth Poe. Please then say hello to user and make an introduction to the user about yourself and your functionailities as a shop assistant.
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
            - 4. You can ask for detail information of a specific cloth item which is recently mentioned.
            """
            output = conversation.predict(input=sorry_input)
            memory.save_context({"input": sorry_input}, {"output": output})
            return jsonify({"response": True, "list": False, "message": output})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "uploadPose":
        upload_instructions = """
            To ensure you have a great experience, kindly upload your images in accepted file formats such as PNG, JPG, or JPEG. When taking the photo, please maintain straight arms for optimal results. To best assist you, the photo should encompass your entire upper body, from head to knee. If you have any questions, feel free to reach out. We're always here to help!
        """
        try:
            instruction_input = """
            You have to provide instructions of how to upload photos based on the following instructions:
            {}. Please do not say thank you the user for giving the instruction.
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
            if len(img_urls) > 5:
                img_urls = random.sample(list(img_urls), k=5)

            if len(img_urls) == 0:
                return jsonify({"message": "Sorry, we cannot find any suitable clothes for you. Can you describe more details ?", "list": False, "response": True})

            data_folder = os.path.join(os.path.dirname(
                os.path.relpath(__file__)), 'data')
            recommend_img = os.path.join(os.path.dirname(os.path.realpath(
                __file__)), 'static', 'recommend_img')

            for img_url in img_urls:
                shutil.copy(data_folder + "/" + img_url, recommend_img)

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
            print("Try on")
            # Copy test_pairs.txt in ChatBot/static/try_on to DM_VTON_new/dataset/VITON-Clean/VITON_test
            shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'try_on', 'test_pairs.txt'),
                        os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'DM_VTON_new', 'dataset', 'VITON-Clean', 'VITON_test'))

            # Remove all images in test_img folder in DM_VTON_new
            test_img = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(
                __file__))), 'DM_VTON_new', 'dataset', 'VITON-Clean', 'VITON_test', 'test_img')
            file_list = os.listdir(test_img)
            for file_name in file_list:
                file_path = os.path.join(test_img, file_name)
                os.remove(file_path)

            # Copy pose image in ChatBot/static/pose to DM_VTON_new/dataset/VITON-Clean/VITON_test
            shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'pose', pose),
                        os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'DM_VTON_new', 'dataset', 'VITON-Clean', 'VITON_test', 'test_img'))

            img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(
                __file__))), 'DM_VTON_new', 'dataset', 'VITON-Clean', 'VITON_test', 'test_img', pose)
            result = tryon(img_path=img_path)
            if result:
                # Copy result try-on image from DM_VTON_new/DMVTON/runs/test/DM-VTON_demo/results/tryon to ChatBot/static/try_on
                result_img = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(
                    __file__))), 'DM_VTON_new', 'DMVTON', 'runs', 'test', 'DM-VTON_demo', 'results', 'tryon')
                file_list = os.listdir(result_img)
                result_path = os.path.join(result_img, file_list[0])
                shutil.copy(result_path, os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), 'static', 'try_on'))

                # Get relative path of result image
                result_img_rel_path = os.path.join(os.path.dirname(
                    os.path.realpath(__file__)), 'static', 'try_on', file_list[0])

                imgs = []
                with open(result_img_rel_path, 'rb') as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    imgs.append(base64_data)

                return jsonify({"message": "Here are the results you've been waiting for! My aim is to ensure your utmost satisfaction with both the outcome and your overall experience. I genuinely hope that the results meet or even exceed your expectations.", "imgs": imgs, "list": True, "response": True})
            else:
                return jsonify({"message": "Sorry, we cannot try on this cloth. Please try another one.", "list": False, "response": True})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

        return jsonify({"message": "Please upload your photo", "list": False, "response": True})

    elif function_name == "predictSize":
        try:
            output_parser = CommaSeparatedListOutputParser()
            format_instructions = output_parser.get_format_instructions()
            prompt = PromptTemplate(
                template="Get 4 {number} include height, weight, age, sex when base on user's input.\n{format_instructions}",
                input_variables=['number'],
                partial_variables={"format_instructions": format_instructions}
            )
            model = OpenAI(temperature=0)
            _input = prompt.format(data=str(user_input))
            output = model(_input)
            # output = conversation.run(input=user_input)
            result = output_parser.parse(output)
            print("-------,", result)
            try:
                Size = predict_new_data(result)
                print('--------', Size)
            except:
                print("Fail")
            return jsonify({"response": True, "list": False, "message": output})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "showDetail":
        if not idx.isdigit():
            return jsonify({"message": "Please specify an approriate position for us.", "list": False, "response": True})
        else:
            idx = int(idx)

        try:
            file_list = os.listdir(os.path.join(os.path.dirname(
                os.path.realpath(__file__)), 'static', 'recommend_img'))
            file_list.sort()

            selected_img = file_list[idx - 1]
            print(selected_img)
            selected_img_path = os.path.join('Cloth', selected_img)
            color, price, rates, url, material = full_info(selected_img_path)

            return jsonify({"message": f"""Here is the information of the cloth item you requested: Color: {color}, Price: {price}, Rates: {rates}, Material: {material}, URL: {url}""", "list": False, "response": True})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})

    elif function_name == "deletePose":
        try:
            # Remove all images in pose folder
            pose_folder = os.path.join(os.path.dirname(os.path.realpath(
                __file__)), 'static', 'pose')
            files = os.listdir(pose_folder)
            for file in files:
                file_path = os.path.join(pose_folder, file)
                os.remove(file_path)

            # Remove all images in try_on folder
            try_on_folder = os.path.join(os.path.dirname(os.path.realpath(
                __file__)), 'static', 'try_on')
            files = os.listdir(try_on_folder)
            for file in files:
                file_path = os.path.join(try_on_folder, file)
                os.remove(file_path)

            # Remove all images in DM_VTON_new/dataset/VITON-Clean/VITON_test/test_img
            test_img_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(
                __file__))), 'DM_VTON_new', 'dataset', 'VITON-Clean', 'VITON_test', 'test_img')
            files = os.listdir(test_img_folder)
            for file in files:
                file_path = os.path.join(test_img_folder, file)
                os.remove(file_path)

            # Remove results folder in DM_VTON_new/DMVTON/runs/test/DM-VTON_demo/results
            results_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(
                __file__))), 'DM_VTON_new', 'DMVTON', 'runs', 'test', 'DM-VTON_demo', 'results')
            shutil.rmtree(results_folder)

            return jsonify({"message": "Your photo has been deleted successfully. Please upload another photo.", "list": False, "response": True})
        except Exception as e:
            return jsonify({"message": str(e), "list": False, "response": False})


@main.route("/chatbot")
@flask_login.login_required
def chatbot():
    return render_template("chatbot.html")


@main.route('/profile')
@flask_login.login_required
def profile():
    user = flask_login.current_user
    return render_template('profile.html', user=user)
