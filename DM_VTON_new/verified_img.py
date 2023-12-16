import os
import cv2
import torch
import albumentations as albu
import numpy as np
from pylab import imshow
from PIL import Image, ImageOps
import mediapipe as mp
from rembg import remove


def calculate_angle(a, b, c):
    cosine_angle = abs(
        (a.x - b.x) * (c.x - b.x) + (a.y - b.y) * (c.y - b.y)
    ) / (
        ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 *
        ((c.x - b.x) ** 2 + (c.y - b.y) ** 2) ** 0.5
    )
    return np.degrees(np.arccos(cosine_angle))


def is_arm_straight(landmarks):
    # Get the landmarks for the shoulder, elbow, and wrist
    left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value]
    left_elbow = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value]
    left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value]
    left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
    right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value]
    right_elbow = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value]
    right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value]
    right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)
    # Define a threshold for what constitutes a straight hand
    straight_threshold = 150  # You might need to adjust this value based on your use case
    # Check if the angle is within the threshold
    left_flag = (left_angle > straight_threshold) or (
        left_angle < 180 - straight_threshold)
    right_flag = (right_angle > straight_threshold) or (
        right_angle < 180 - straight_threshold)
    return left_flag and right_flag


# def check_arm_straight(image_path):
#     # Initialize MediaPipe Pose
#     mp_pose = mp.solutions.pose
#     pose = mp_pose.Pose(static_image_mode=True,
#                         min_detection_confidence=0.5, min_tracking_confidence=0.5)
#     # Read an image
#     image = cv2.imread(image_path)
#     # Process the image
#     results = pose.process(image)
#     if results.pose_landmarks:
#         landmarks = results.pose_landmarks.landmark
#         return is_arm_straight(landmarks)
#     return -1  # Error


# Use function verified_input
# def verified_input(image_name):
#     data_folder = '../dataset/VITON-Clean/VITON_test'
#     input = Image.open(os.path.join(data_folder, 'test_img', image_name))
#     output = remove(input, bgcolor=(255, 255, 255, 0)).convert('RGB')
#     output.save(os.path.join(data_folder, 'test_img', 'removebg_img.jpg'))

#     if check_arm_straight(os.path.join(data_folder, 'test_img', 'removebg_img.jpg')) == 0:
#         print("Unaccepted!")
#         return False
#     else:
#         return True

def check_arm_straight(image):
    # Initialize MediaPipe Pose
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=True,
                        min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Convert the image to cv2
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Process the image
    results = pose.process(image)
    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        return is_arm_straight(landmarks)
    return -1  # Error


def verified_input(image):
    output = remove(image, bgcolor=(255, 255, 255, 0)).convert('RGB')

    if check_arm_straight(output) == 0:
        return False
    else:
        return True