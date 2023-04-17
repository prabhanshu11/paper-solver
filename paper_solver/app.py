# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_gradio_app.ipynb.

# %% auto 0
__all__ = ['model', 'model_id', 'label2color', 'data_dir', 'image', 'encoding', 'outputs', 'predictions', 'labels', 'ocr_text',
           'predicted_labels', 'ocr_with_labels', 'unnormalize_box', 'draw_boxes', 'run_inference']

# %% ../nbs/04_gradio_app.ipynb 3
import torch
import numpy as np
import pandas as pd
from transformers import LiltForTokenClassification, LayoutLMv3Processor
from transformers import LayoutLMv3FeatureExtractor, AutoTokenizer, LayoutLMv3Processor
from PIL import Image, ImageDraw, ImageFont
# Project specific objects
from .preprocess import *

# %% ../nbs/04_gradio_app.ipynb 7
model = LiltForTokenClassification.from_pretrained(OUTPUT_PATH/'LiLTmodel')
model_id="SCUT-DLVCLab/lilt-roberta-en-base"

# %% ../nbs/04_gradio_app.ipynb 14
def unnormalize_box(bbox, width, height):
    return [width * (bbox[0] / 1000), height * (bbox[1] / 1000),
            width * (bbox[2] / 1000), height * (bbox[3] / 1000)]

label2color = {
    'I-Q': 'blue',
    'O': 'black',
    'E-TABLE': 'yellow',
    'B-SUB-SUB-Q': 'green',
    'B-SUB-Q': 'darkgreen',
    'S-CHART': 'purple',
    'B-TABLE': 'orange',
    'E-SUB-Q': 'darkgreen',
    'I-SUB-Q': 'green',
    'I-TABLE': 'gold',
    'B-Q': 'red',
    'B-CHART': 'magenta',
    'E-CHART': 'pink',
    'I-SUB-SUB-Q': 'darkblue',
    'E-Q': 'maroon',
    'E-SUBJECT NAME': 'cyan',
    'E-SUB-SUB-Q': 'darkred',
    'B-SUBJECT NAME': 'lightblue',
    'I-CHART': 'violet'
}

# draw results onto the image
def draw_boxes(image, boxes, predictions):
    width, height = image.size
    normalizes_boxes = [unnormalize_box(box, width, height) for box in boxes]

    # draw predictions over the image
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    for prediction, box in zip(predictions, normalizes_boxes):
        if prediction == "O":
            continue
        draw.rectangle(box, outline="black")
        draw.rectangle(box, outline=label2color[prediction])
        draw.text((box[0] + 10, box[1] - 10), text=prediction, fill=label2color[prediction], font=font)
    return image

# %% ../nbs/04_gradio_app.ipynb 15
def run_inference(image, model=model, processor=processor, output_image=True):
    # create model input
    encoding = processor(image, return_tensors="pt")
    del encoding["pixel_values"]
    # run inference
    outputs = model(**encoding)
    predictions = outputs.logits.argmax(-1).squeeze().tolist()
    # get labels
    labels = [model.config.id2label[prediction] for prediction in predictions]
    if output_image:
        return draw_boxes(image, encoding["bbox"][0], labels)
    else:
        return labels

# %% ../nbs/04_gradio_app.ipynb 17
data_dir = PROJECT_HOME/'data/doc-scanner/5fe15b06-ee59-4461-9f88-505f3e4b2696'

# %% ../nbs/04_gradio_app.ipynb 18
from PIL import Image, ImageDraw, ImageFont

image = Image.open(data_dir/'page_6_image_0.jpg')
image = image.convert("RGB")
image.resize((350,450))

# %% ../nbs/04_gradio_app.ipynb 20
encoding = processor(image, return_tensors="pt")
del encoding["pixel_values"]
# run inference
outputs = model(**encoding)
predictions = outputs.logits.argmax(-1).squeeze().tolist()
# get labels
labels = [model.config.id2label[prediction] for prediction in predictions]
#draw_boxes(image, encoding["bbox"][0], labels)

# %% ../nbs/04_gradio_app.ipynb 21
# extract OCR text
ocr_text = tokenizer.decode(encoding.input_ids[0])
# extract labels
predicted_labels = []
for pred in predictions:
    predicted_labels.append(model.config.id2label[pred])
# zip OCR text with corresponding labels
ocr_with_labels = list(zip(ocr_text.split(), predicted_labels))
print('ocr_text', ocr_text)
