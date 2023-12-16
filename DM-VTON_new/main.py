import os
import cv2
import torch
import albumentations as albu
import numpy as np
from pylab import imshow
from PIL import Image, ImageOps
import mediapipe as mp
from rembg import remove 
from iglovikov_helper_functions.utils.image_utils import load_rgb, pad, unpad
from iglovikov_helper_functions.dl.pytorch.utils import tensor_from_rgb_image
from cloths_segmentation.pre_trained_models import create_model

model = create_model("Unet_2020-10-30")
model.eval();

def calculate_angle(a, b, c):
  cosine_angle = abs(
        (a.x - b.x) * (c.x - b.x) + (a.y - b.y) * (c.y - b.y)
    ) / (
        ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5 * ((c.x - b.x) ** 2 + (c.y - b.y) ** 2) ** 0.5
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
    left_flag = (left_angle > straight_threshold) or (left_angle < 180 - straight_threshold)
    right_flag = (right_angle > straight_threshold) or (right_angle < 180 - straight_threshold)
    return left_flag and right_flag

def check_arm_straight(image_path):
  # Initialize MediaPipe Pose
  mp_pose = mp.solutions.pose
  pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5, min_tracking_confidence=0.5)
  # Read an image
  image = cv2.imread(image_path)
  # Process the image
  results = pose.process(image)
  if results.pose_landmarks:
    landmarks = results.pose_landmarks.landmark
    return is_arm_straight(landmarks)
  return -1 #Error

def preprocessing(img_name = "000001_1.jpg", color_name = "000001_0.jpg"):
    """
    Preprocessing Image and Cloth with:
    + Remove background
    + Create mask for cloth
    + Resize and padding if needed
    """

    # Create Path (Change data_folder if needed)
    data_folder = '../dataset/VITON-Clean/VITON_test'
    color_path = os.path.join(data_folder, "test_color", color_name)
    edge_path = os.path.join(data_folder, "test_edge", color_name)
    img_path = os.path.join(data_folder, "test_img", img_name)

    # Remove background of Image
    input = Image.open(img_path) 
    output = remove(input, bgcolor = (255,255,255,0)).convert('RGB')  
    output.save(img_path)

    # Create mask for Color
    image = load_rgb(color_path)
    if image.shape != (256,192,3):
      transform = albu.Compose([albu.Normalize(p=1)], p=1)
      padded_image, pads = pad(image, factor=32, border=cv2.BORDER_CONSTANT)
      x = transform(image=padded_image)["image"]
      x = torch.unsqueeze(tensor_from_rgb_image(x), 0)
      with torch.no_grad():
          prediction = model(x)[0][0]
      mask = (prediction > 0).cpu().numpy().astype(np.uint8)
      mask = unpad(mask, pads)
      cv2.imwrite(edge_path, cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB) * 255)

    # Resize Color and Edge
    expected_size = (192,256)
    edge = cv2.imread(edge_path)
    color = cv2.imread(color_path)
    if edge.shape != (256,192,3):
        blurred = cv2.blur(edge, (3,3))
        canny = cv2.Canny(blurred, 50, 200)
        pts = np.argwhere(canny>0)
        y1,x1 = pts.min(axis=0)
        y2,x2 = pts.max(axis=0)     
        edge = edge[y1-20:y2+20, x1-15:x2+15]
        color = color[y1-20:y2+20, x1-15:x2+15]
        edge = Image.fromarray(cv2.cvtColor(edge, cv2.COLOR_BGR2RGB))
        color = Image.fromarray(cv2.cvtColor(color, cv2.COLOR_BGR2RGB))
        edge.thumbnail((expected_size[0], expected_size[1]))
        color.thumbnail((expected_size[0], expected_size[1]))
        delta_width = expected_size[0] - edge.size[0]
        delta_height = expected_size[1] - edge.size[1]
        pad_width = delta_width // 2
        pad_height = delta_height // 2
        padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
        edge = ImageOps.expand(edge, padding, fill = (0, 0, 0))
        color = ImageOps.expand(color, padding, fill = (234, 238, 239))
        edge.save(edge_path)
        color.save(color_path)
    
    # Resize Image
    img = cv2.imread(img_path)
    if img.shape != (256,192,3):
        blurred = cv2.blur(img, (3,3))
        canny = cv2.Canny(blurred, 50, 200)
        pts = np.argwhere(canny>0)
        y1,x1 = pts.min(axis=0)
        y2,x2 = pts.max(axis=0)     
        img = img[y1-20:y2+20, x1-15:x2+15]
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        img.thumbnail((expected_size[0], expected_size[1]))
        delta_width = expected_size[0] - img.size[0]
        delta_height = expected_size[1] - img.size[1]
        pad_width = delta_width // 2
        pad_height = delta_height // 2
        padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
        img = ImageOps.expand(img, padding, fill = (255, 255, 255))
        img.save(img_path)

def tryon(img_name = "000001_1.jpg", color_name = "000001_0.jpg"):
  data_folder = '../dataset/VITON-Clean/VITON_test'
  f = open(f"{data_folder}/test_pairs.txt", "w")
  f.write(f"{img_name} {color_name}")
  f.close()
  if check_arm_straight(os.path.join(data_folder,'test_img', img_name)) == 0:
    print("Unaccepted!")
    return -1
  else: 
    preprocessing(img_name, color_name)
    os.system("""py test.py --project runs/test --name DM-VTON_demo \
              --device 0 --align_corners --batch_size 1 --workers 0 \
              --dataroot ../dataset/VITON-Clean/VITON_test \
              --pf_warp_checkpoint checkpoints/dmvton_pf_warp.pt \
              --pf_gen_checkpoint checkpoints/dmvton_pf_gen.pt
              """)
    im = Image.open(f"./runs/test/DM-VTON_demo/results/tryon/{img_name}")
    im.show()
    return 0
  # Path result: ./runs/test/DM-VTON_demo/results/tryon/000001_0.jpg
    
if __name__ == "__main__":
   # cwd: D://Datathong//DM-VTON_new
   os.chdir("DMVTON")
   results = tryon("000041_0.jpg", "000102_1.jpg")