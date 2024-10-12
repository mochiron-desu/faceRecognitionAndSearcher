import cv2
import os
import numpy as np
import logging
from database import connect_to_db, encode_face, find_similar_face, save_face_to_db
import face_recognition

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def extract_faces(image_path):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    return face_locations, image

def save_unique_face(face_location, image, unique_faces_folder, face_id):
    top, right, bottom, left = face_location
    face_image = image[top:bottom, left:right]
    face_filename = f"{face_id}.jpg"
    face_path = os.path.join(unique_faces_folder, face_filename)
    cv2.imwrite(face_path, cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))
    return face_path

def process_images(image_folder, unique_faces_folder, collection):
    unique_face_count = 0
    face_occurrences = {}

    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            logging.info(f"Processing image: {filename}")
            image_path = os.path.join(image_folder, filename)
            face_locations, image = extract_faces(image_path)

            for face_location in face_locations:
                face_encoding = face_recognition.face_encodings(image, [face_location])[0]
                encoded_face = encode_face(face_encoding)
                
                existing_face_id = find_similar_face(collection, face_encoding)

                if existing_face_id is None:
                    face_id = unique_face_count
                    face_path = save_unique_face(face_location, image, unique_faces_folder, face_id)
                    
                    face_data = {
                        'face_id': face_id,
                        'image_filename': face_path,
                        'face_encoding': encoded_face,
                        'occurrences': [{
                            'filename': filename,
                            'bounding_box': face_location
                        }]
                    }

                    save_face_to_db(collection, face_data)
                    logging.info(f"Saved unique face ID {face_id} to database with path: {face_path}")
                    
                    face_occurrences[face_id] = [{
                        'filename': filename,
                        'bounding_box': face_location
                    }]
                    unique_face_count += 1
                else:
                    logging.info(f"Found existing face ID {existing_face_id} in image: {filename}")
                    # Update the occurrences for the existing face
                    collection.update_one(
                        {'face_id': existing_face_id},
                        {'$push': {'occurrences': {
                            'filename': filename,
                            'bounding_box': face_location
                        }}}
                    )
                    if existing_face_id in face_occurrences:
                        face_occurrences[existing_face_id].append({
                            'filename': filename,
                            'bounding_box': face_location
                        })
                    else:
                        face_occurrences[existing_face_id] = [{
                            'filename': filename,
                            'bounding_box': face_location
                        }]

    return unique_face_count, face_occurrences

if __name__ == "__main__":
    image_folder = 'images'
    unique_faces_folder = 'unique_faces'

    collection = connect_to_db()

    if not os.path.exists(unique_faces_folder):
        os.makedirs(unique_faces_folder)

    unique_faces_count, face_occurrences = process_images(image_folder, unique_faces_folder, collection)
    logging.info(f"Unique faces extracted and saved to database: {unique_faces_count}")
    logging.info(f"Face occurrences: {face_occurrences}")