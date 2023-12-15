import os
relative_path = "ChatBot/static/000003_1.jpg"
absolute_path = os.path.join(os.path.dirname(
    os.path.relpath(__file__)), 'static')
print(absolute_path)
