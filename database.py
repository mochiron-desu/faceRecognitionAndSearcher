# database.py
from pymongo import MongoClient
import face_recognition
import base64
import numpy as np
import cv2
import logging

FACE_SIMILARITY_TOLARANCE = 0.55

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Log to a file
        logging.StreamHandler()  # Log to console
    ]
)

def connect_to_db():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['face_recognition_db']
    logging.info("Connected to MongoDB database.")
    return db['faces_collection']

def save_face_to_db(collection, face_data):
    logging.info(f"Saving face {face_data['face_id']} to database.")
    collection.insert_one(face_data)

def find_similar_face(collection, face_encoding, tolerance=FACE_SIMILARITY_TOLARANCE):
    logging.info("Searching for similar face in the database.")
    results = collection.find()
    for result in results:
        existing_encoding = np.frombuffer(base64.b64decode(result["face_encoding"]), np.float64)
        matches = face_recognition.compare_faces([existing_encoding], face_encoding, tolerance=tolerance)
        if matches[0]:  # If there is a match
            logging.info(f"Found similar face: {result['face_id']}")
            return result['face_id']
    logging.info("No similar face found.")
    return None

def encode_face(face_encoding):
    return base64.b64encode(face_encoding.tobytes()).decode('utf-8')