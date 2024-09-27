import os
import pickle

import numpy as np

with open(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attribute_model', 'scaler.pkl'), mode='rb') as file:
    loaded_scaler = pickle.load(file)

with open(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'attribute_model', 'voting_classifier.pkl'), mode='rb') as file:
    loaded_voting_classifier = pickle.load(file)


def get_number(input_string):
    # Split the input string into words
    words = input_string.split()

    # Extract numbers from the words
    numbers = [float(word)
               for word in words if word.replace('.', '').isdigit()]
    return float(numbers)

def predict_new_data(X_new_list, scaler=loaded_scaler, loaded_classifier=loaded_voting_classifier):
    # Assuming X_new_list is a list of data points, each represented as a list [feature1, feature2, ..., feature_n]
    height, weight, age, sex = X_new_list
    height = get_number(height)
    weight = get_number(weight)
    age = get_number(age)
    if str(sex).lower() == 'male':
        sex = 1
    else:
        sex = 0 
    X_new = np.array([height, weight, age, sex]).reshape(
        len(X_new_list), -1)  # Reshape to a 2D array

    # Scale the new data using the provided scaler
    X_new_scaled = scaler.transform(X_new)

    # Make predictions on the new data using the loaded classifier
    y_pred_new_list = loaded_classifier.predict(X_new_scaled)

    return y_pred_new_list


if __name__ == "__main__":
    # Height, weight, age, sex (1: Male, 0: Female)
    X_new_list = [
        [180, 65, 22, 1],
        # Add more data points as needed
    ]

    # Use the function to get predictions
    y_pred_new_list = predict_new_data(
        X_new_list, loaded_scaler, loaded_voting_classifier)
    print(y_pred_new_list)
