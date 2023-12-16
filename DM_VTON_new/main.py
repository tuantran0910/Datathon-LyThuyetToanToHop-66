import os
import cv2
import torch
import albumentations as albu
import numpy as np
from pylab import imshow
from PIL import Image, ImageOps
import mediapipe as mp
from rembg import remove

# def preprocessing(img_name = "000001_1.jpg", color_name = "000001_0.jpg"):
#     """
#     Preprocessing Image and Cloth with:
#     + Remove background
#     + Create mask for cloth
#     + Resize and padding if needed
#     """

#     # Create Path (Change data_folder if needed)
#     data_folder = '../dataset/VITON-Clean/VITON_test'
#     color_path = os.path.join(data_folder, "test_color", color_name)
#     edge_path = os.path.join(data_folder, "test_edge", color_name)
#     img_path = os.path.join(data_folder, "test_img", img_name)

#     # Remove background of Image
#     input = Image.open(img_path)
#     output = remove(input, bgcolor = (255,255,255,0)).convert('RGB')
#     output.save(img_path)

#     # Create mask for Color
#     image = load_rgb(color_path)
#     if image.shape != (256,192,3):
#       transform = albu.Compose([albu.Normalize(p=1)], p=1)
#       padded_image, pads = pad(image, factor=32, border=cv2.BORDER_CONSTANT)
#       x = transform(image=padded_image)["image"]
#       x = torch.unsqueeze(tensor_from_rgb_image(x), 0)
#       with torch.no_grad():
#           prediction = model(x)[0][0]
#       mask = (prediction > 0).cpu().numpy().astype(np.uint8)
#       mask = unpad(mask, pads)
#       cv2.imwrite(edge_path, cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB) * 255)

#     # Resize Color and Edge
#     expected_size = (192,256)
#     edge = cv2.imread(edge_path)
#     color = cv2.imread(color_path)
#     if edge.shape != (256,192,3):
#         blurred = cv2.blur(edge, (3,3))
#         canny = cv2.Canny(blurred, 50, 200)
#         pts = np.argwhere(canny>0)
#         y1,x1 = pts.min(axis=0)
#         y2,x2 = pts.max(axis=0)
#         edge = edge[y1-20:y2+20, x1-15:x2+15]
#         color = color[y1-20:y2+20, x1-15:x2+15]
#         edge = Image.fromarray(cv2.cvtColor(edge, cv2.COLOR_BGR2RGB))
#         color = Image.fromarray(cv2.cvtColor(color, cv2.COLOR_BGR2RGB))
#         edge.thumbnail((expected_size[0], expected_size[1]))
#         color.thumbnail((expected_size[0], expected_size[1]))
#         delta_width = expected_size[0] - edge.size[0]
#         delta_height = expected_size[1] - edge.size[1]
#         pad_width = delta_width // 2
#         pad_height = delta_height // 2
#         padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
#         edge = ImageOps.expand(edge, padding, fill = (0, 0, 0))
#         color = ImageOps.expand(color, padding, fill = (234, 238, 239))
#         edge.save(edge_path)
#         color.save(color_path)

#     # Resize Image
#     img = cv2.imread(img_path)
#     if img.shape != (256,192,3):
#         blurred = cv2.blur(img, (3,3))
#         canny = cv2.Canny(blurred, 50, 200)
#         pts = np.argwhere(canny>0)
#         y1,x1 = pts.min(axis=0)
#         y2,x2 = pts.max(axis=0)
#         img = img[y1-20:y2+20, x1-15:x2+15]
#         img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
#         img.thumbnail((expected_size[0], expected_size[1]))
#         delta_width = expected_size[0] - img.size[0]
#         delta_height = expected_size[1] - img.size[1]
#         pad_width = delta_width // 2
#         pad_height = delta_height // 2
#         padding = (pad_width, pad_height, delta_width - pad_width, delta_height - pad_height)
#         img = ImageOps.expand(img, padding, fill = (255, 255, 255))
#         img.save(img_path)


def tryon(img_path="000001_0.jpg", cloth_path="000001_1.jpg"):
    # Remove background
    input = Image.open(img_path)
    output = remove(input, bgcolor=(255, 255, 255, 0)).convert('RGB')
    # output.save(img_path)

    # Resize Image
    expected_size = (192, 256)
    # Convert PIL to cv2
    output = cv2.cvtColor(np.array(output), cv2.COLOR_RGB2BGR)

    if output.shape != (256, 192, 3):
        blurred = cv2.blur(output, (3, 3))
        canny = cv2.Canny(blurred, 50, 200)
        pts = np.argwhere(canny > 0)
        y1, x1 = pts.min(axis=0)
        y2, x2 = pts.max(axis=0)
        img = output[y1-20:y2+20, x1-15:x2+15]
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        img.thumbnail((expected_size[0], expected_size[1]))
        delta_width = expected_size[0] - img.size[0]
        delta_height = expected_size[1] - img.size[1]
        pad_width = delta_width // 2
        pad_height = delta_height // 2
        padding = (pad_width, pad_height, delta_width -
                   pad_width, delta_height - pad_height)
        img = ImageOps.expand(img, padding, fill=(255, 255, 255))
        img.save("000001_0_resize.jpg")

    os.system("""python DM_VTON_new/DMVTON/test.py --project runs/test --name DM-VTON_demo \
              --device 0 --align_corners --batch_size 1 --workers 0 \
              --dataroot ../dataset/VITON-Clean/VITON_test \
              --pf_warp_checkpoint checkpoints/dmvton_pf_warp.pt \
              --pf_gen_checkpoint checkpoints/dmvton_pf_gen.pt
              """)
    return 0


if __name__ == "__main__":
    # cwd: D://Datathong//DM-VTON_new
    tryon()
