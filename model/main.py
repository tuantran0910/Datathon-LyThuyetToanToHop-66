import os
import cv2
import torch
import albumentations as albu
import numpy as np
from pylab import imshow
from PIL import Image, ImageOps
import mediapipe as mp
from rembg import remove


def tryon(img_path="000001_0.jpg"):
    try:
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
            img.save(img_path)

        os.system("""python DM_VTON_new/DMVTON/test.py --project DM_VTON_new/DMVTON/runs/test --name DM-VTON_demo \
                --device 0 --align_corners --batch_size 1 --workers 1 \
                --dataroot DM_VTON_new/dataset/VITON-Clean/VITON_test \
                --pf_warp_checkpoint DM_VTON_new/DMVTON/checkpoints/dmvton_pf_warp.pt \
                --pf_gen_checkpoint DM_VTON_new/DMVTON/checkpoints/dmvton_pf_gen.pt
                """)
        return True
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":
    # cwd: D://Datathong//DM-VTON_new
    tryon()
