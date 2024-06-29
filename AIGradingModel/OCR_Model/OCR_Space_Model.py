from PIL import Image
import requests
import cv2
import numpy as np
import os
import json

def Segment_Paper(file):
    # Constants
    KNOWN_LINE_DISTANCE_CM = 0.5  # Known distance between lines in cm
    PIXELS_PER_CM = 96 / 2.54  

    # Read the image
    img = cv2.imread(file)
    if img is None:
        print("Error: Image not loaded correctly.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply binary thresholding
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Apply morphological operations to close gaps in the text lines
    kernel = np.ones((5, 5), np.uint8)
    morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Calculate horizontal projection profile
    hist = cv2.reduce(morph, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32S).reshape(-1)

    # Determine the number of pixels corresponding to the known line distance
    line_distance_pixels = int(KNOWN_LINE_DISTANCE_CM * PIXELS_PER_CM)

    # Initialize boundaries
    uppers = []
    lowers = []
    in_text = False

    for i, value in enumerate(hist):
        if value > 0 and not in_text:
            uppers.append(i)
            in_text = True
        elif value == 0 and in_text:
            lowers.append(i)
            in_text = False

    # Refine boundaries based on known line distance
    refined_uppers = []
    refined_lowers = []

    for i in range(len(uppers)):
        if i == 0 or (uppers[i] - refined_uppers[-1] >= line_distance_pixels):
            refined_uppers.append(uppers[i])
            refined_lowers.append(lowers[i])

    # Draw boundaries on the original image for visualization
    visualization_img = img.copy()
    for upper in refined_uppers:
        cv2.line(visualization_img, (0, upper), (img.shape[1], upper), (0, 255, 0), 2)
    for lower in refined_lowers:
        cv2.line(visualization_img, (0, lower), (img.shape[1], lower), (255, 0, 0), 2)

    # Initialize a list to store lines
    lines = []

    # Extract lines based on refined upper and lower boundaries
    for upper, lower in zip(refined_uppers, refined_lowers):
        line_img = img[upper:lower, :]
        if line_img.size > 0:  # Check if the image is not empty
            lines.append(line_img)

    cv2.destroyAllWindows()
    return lines

def ocr_space_file(file, overlay=False, api_key='1b70baf52f88957', language='eng'):

        payload = {'isOverlayRequired': overlay,
                  'apikey': api_key,
                  'language': language,
                  'detectOrientation': 'true',
                  'scale' : 'true',
                  'OCREngine': 2,
                  }
        # Save the image to a temporary file
        temp_filename = "temp_image.png"
        file.save(temp_filename)

        with open(temp_filename, 'rb') as f:
            r = requests.post('https://api.ocr.space/parse/image',
                              files={temp_filename: f},
                              data=payload,
                              )
        # Remove the temporary file
        os.remove(temp_filename)

        return r.content.decode()

def OCR_Space_Model(file):
    images = Segment_Paper(file)

    extracted_ID   = json.loads(ocr_space_file(file = Image.fromarray(images[0]).convert("RGB"), language='eng'))
    extracted_Name = json.loads(ocr_space_file(file = Image.fromarray(images[1]).convert("RGB"), language='eng'))

    student_ID   = extracted_ID["ParsedResults"][0]["ParsedText"]
    student_ID   = student_ID.replace('ID:', '').replace('1D:','').replace(' ', '').replace('\n', '')

    student_Name = extracted_Name["ParsedResults"][0]["ParsedText"]
    student_Name   = student_Name.replace('Name:', '')

    answer = images[2:]
    student_answer = ""
    
    for i in range(len(answer)):
        answer_text_json = json.loads(ocr_space_file(file = Image.fromarray(answer[i]).convert("RGB"), language='eng'))

        if answer_text_json.get('OCRExitCode') == 1:
            extracted_answer = answer_text_json["ParsedResults"][0]["ParsedText"]

            if not extracted_answer.strip():
                student_answer += ""
            else:
                student_answer += "\n" + extracted_answer.replace('Answer:', '')
        else:
          student_answer+=""

    return student_ID, student_Name , student_answer
