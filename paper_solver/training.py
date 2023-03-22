# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_training.ipynb.

# %% auto 0
__all__ = ['train_dataset', 'eval_dataset', 'train_raw_dataset', 'eval_raw_dataset', 'label_list', 'num_labels', 'label2id',
           'id2label', 'model_id', 'model', 'metric', 'return_entity_level_metrics', 'NUM_TRAIN_EPOCHS',
           'PER_DEVICE_TRAIN_BATCH_SIZE', 'PER_DEVICE_EVAL_BATCH_SIZE', 'LEARNING_RATE', 'training_args', 'trainer',
           'compute_metrics']

# %% ../nbs/02_training.ipynb 5
import torch
import numpy as np
import pandas as pd
from datasets import load_metric
from transformers import TrainingArguments, Trainer
from transformers import LayoutLMv3ForTokenClassification,AutoProcessor
from transformers.data.data_collator import default_data_collator
from typing import Union
# Project specific objects
from .preprocess import *

# %% ../nbs/02_training.ipynb 6
from datasets import load_from_disk
train_dataset = load_from_disk(OUTPUT_PATH/'train_split')
eval_dataset = load_from_disk(OUTPUT_PATH/'eval_split')

# %% ../nbs/02_training.ipynb 7
## Loading raw dataset without Encoding or applying feature extractor
train_raw_dataset = load_from_disk(OUTPUT_PATH/'raw_data/train')
eval_raw_dataset = load_from_disk(OUTPUT_PATH/'raw_data/test')

# %% ../nbs/02_training.ipynb 12
label_list = train_dataset.features["labels"].feature.names
num_labels = len(label_list)
label2id, id2label = dict(), dict()
for i, label in enumerate(label_list):
    label2id[label] = i
    id2label[i] = label

# %% ../nbs/02_training.ipynb 13
from transformers import LiltForTokenClassification
model_id = "SCUT-DLVCLab/lilt-roberta-en-base"
# load model with correct number of labels and mapping
model = LiltForTokenClassification.from_pretrained(
    model_id, num_labels=len(label_list), label2id=label2id, id2label=id2label
)


# %% ../nbs/02_training.ipynb 15
metric = load_metric("seqeval")
return_entity_level_metrics = False

def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    # Remove ignored index (special tokens)
    true_predictions = [
        [label_list[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [label_list[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    results = metric.compute(
        predictions=true_predictions, 
        references=true_labels,
        zero_division='0'
    )
    if return_entity_level_metrics:
        final_results = {}
        for key, value in results.items():
            if isinstance(value, dict):
                for n, v in value.items():
                    final_results[f"{key}_{n}"] = v
            else:
                final_results[key] = value
        return final_results
    else:
        return {
            "precision": results["overall_precision"],
            "recall": results["overall_recall"],
            "f1": results["overall_f1"],
            "accuracy": results["overall_accuracy"],
        }

# %% ../nbs/02_training.ipynb 17
from transformers import Trainer, TrainingArguments
NUM_TRAIN_EPOCHS = 100
PER_DEVICE_TRAIN_BATCH_SIZE = 4
PER_DEVICE_EVAL_BATCH_SIZE = 4
LEARNING_RATE = 4e-5
training_args = TrainingArguments(output_dir="LiLT_INVOICE",
                                  # max_steps=1500,
                                  num_train_epochs=NUM_TRAIN_EPOCHS,
                                  logging_strategy="epoch",
                                  save_total_limit=1,
                                  per_device_train_batch_size=PER_DEVICE_TRAIN_BATCH_SIZE,
                                  per_device_eval_batch_size=PER_DEVICE_EVAL_BATCH_SIZE,
                                  learning_rate=LEARNING_RATE,
                                  evaluation_strategy="no",
                                  save_strategy="no",
                                  # eval_steps=100,
                                  load_best_model_at_end=True,
                                  metric_for_best_model="f1")

# Initialize our Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    data_collator=default_data_collator,
    compute_metrics=compute_metrics,
)


# %% ../nbs/02_training.ipynb 18
assert torch.cuda.is_available()
import gc
torch.cuda.empty_cache()
gc.collect()

# %% ../nbs/02_training.ipynb 20
trainer.train()

# %% ../nbs/02_training.ipynb 22
trainer.evaluate()

# %% ../nbs/02_training.ipynb 24
trainer.save_model(OUTPUT_PATH/'LiLTmodel')