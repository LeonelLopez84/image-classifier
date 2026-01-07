import json
import os
import time

import numpy as np
import redis
import settings
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import decode_predictions, preprocess_input
from tensorflow.keras.preprocessing import image

# TODO
# Connect to Redis and assign to variable `db``
# Make use of settings.py module to get Redis settings like host, port, etc.
# Conexión a Redis usando los settings
db = redis.Redis(
    host=settings.REDIS_IP, 
    port=settings.REDIS_PORT, 
    db=settings.REDIS_DB_ID
)

# TODO
# Load your ML model and assign to variable `model`
# See https://drive.google.com/file/d/1ADuBSE4z2ZVIdn66YDSwxKv-58U7WEOn/view?usp=sharing
# for more information about how to use this model.
def load_model():
    """
    load model ResNet50. If doesn't exists will download
    """
    # We use absolute route inside container
    model_path = "/src/resnet50_model.h5"
    
    if os.path.exists(model_path):
        # It's crucial to use compile=False if we only going to predict
        model = tf.keras.models.load_model(model_path, compile=False)
    else:
        # Load the model
        model = ResNet50(weights="imagenet")
        model.save(model_path)
        
    return model

# load the model globally when we start the service
model = load_model()


def predict(image_name):
    """
    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.

    Parameters
    ----------
    image_name : str
        Image filename.

    Returns
    -------
    class_name, pred_probability : tuple(str, float)
        Model predicted class as a string and the corresponding confidence
        score as a number.
    """
    prediction = None
    score = None
    # TODO: Implement the code to predict the class of the image_name

    # Load image

    # Apply preprocessing (convert to numpy array, match model input dimensions (including batch) and use the resnet50 preprocessing)

    # Get predictions using model methods and decode predictions using resnet50 decode_predictions
    #_, class_name, pred_probability = None
    # Convert probabilities to float and round it

    img_path = os.path.join(settings.UPLOAD_FOLDER, image_name)
    
    # load and proprocesing
    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    
    # predict
    preds = model.predict(x)
    # decode_predictions returns [ID, class, score]
    _, class_name, pred_probability = decode_predictions(preds, top=1)[0][0]
    
    return str(class_name), float(pred_probability)

def classify_process():
    """
    Loop indefinitely asking Redis for new jobs.
    When a new job arrives, takes it from the Redis queue, uses the loaded ML
    model to get predictions and stores the results back in Redis using
    the original job ID so other services can see it was processed and access
    the results.

    Load image from the corresponding folder based on the image name
    received, then, run our ML model to get predictions.
    """
    while True:
        # Inside this loop you should add the code to:
        #   1. Take a new job from Redis
        #   2. Run your ML model on the given data
        #   3. Store model prediction in a dict with the following shape:
        #      {
        #         "prediction": str,
        #         "score": float,
        #      }
        #   4. Store the results on Redis using the original job ID as the key
        #      so the API can match the results it gets to the original job
        #      sent
        # Hint: You should be able to successfully implement the communication
        #       code with Redis making use of functions `brpop()` and `set()`.
        # TODO
        # Take a new job from Redis

        # Decode the JSON data for the given job

        # Important! Get and keep the original job ID

        # Run the loaded ml model (use the predict() function)

        # Prepare a new JSON with the results
        # output = {"prediction": None, "score": None}

        # Store the job results on Redis using the original
        # job ID as the key

        queue_name = settings.REDIS_QUEUE
        _, job_data_raw = db.brpop(queue_name)
        job_data = json.loads(job_data_raw)
        
        # Extract data from the job
        image_name = job_data["image_name"]
        job_id = job_data["id"]
        
        # Execute prediction
        prediction, score = predict(image_name)
        
        # Save result in Redis with the Job ID so the API can find it 
        result = {
            "prediction": prediction,
            "score": score
        }
        db.set(job_id, json.dumps(result))

        # Sleep for a bit
        time.sleep(settings.SERVER_SLEEP)


if __name__ == "__main__":
    # Now launch process
    print("Launching ML service...")
    classify_process()
