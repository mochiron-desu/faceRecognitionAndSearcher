import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
from PIL import Image, ImageTk, ImageDraw
import os
import logging
from database import connect_to_db
from search import search_faces_by_id, get_all_face_ids
import face_recognition
import threading
import queue

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

class FaceSearchApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Face Search")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f5f5f5")

        self.collection = connect_to_db()
        
        self.face_frames = []
        self.face_ids = []
        self.selected_face_index = None

        self.create_widgets()
        self.load_faces()

    def create_widgets(self):
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(1, weight=1)

        # Title
        title_label = tk.Label(self.master, text="Face Search", font=("Helvetica", 28, "bold"), bg="#f5f5f5", fg="#333333")
        title_label.grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # Main frame
        main_frame = tk.Frame(self.master, bg="#ffffff", bd=0, highlightthickness=0)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Faces frame with scrollbar
        self.canvas = tk.Canvas(main_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.images_frame = tk.Frame(self.canvas, bg="#ffffff")

        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.create_window((0, 0), window=self.images_frame, anchor="nw")
        self.images_frame.bind("<Configure>", self.on_frame_configure)

        # Search button
        style = ttk.Style()
        style.configure("TButton", padding=10, font=("Helvetica", 12))
        style.configure("Search.TButton", background="#4CAF50", foreground="white")
        self.search_button = ttk.Button(self.master, text="Search Selected Face", command=self.search_selected_face, style="Search.TButton")
        self.search_button.grid(row=2, column=0, pady=20)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_faces(self):
        unique_faces_folder = './unique_faces'
        for filename in os.listdir(unique_faces_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.display_face(filename)

    def display_face(self, filename):
        face_id = os.path.splitext(filename)[0]

        frame = tk.Frame(self.images_frame, bg="#ffffff", bd=0, highlightthickness=0)

        # Track the total number of images and calculate row and column for the grid
        total_faces = len(self.face_frames)
        row = total_faces // 5  # 5 columns per row
        column = total_faces % 5

        frame.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

        image_path = os.path.join('./unique_faces', filename)
        try:
            image = Image.open(image_path)
            image.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(image)

            label = tk.Label(frame, image=photo, bg="#ffffff")
            label.image = photo
            label.pack(padx=5, pady=5)

            id_label = tk.Label(frame, text=f"ID: {face_id}", bg="#ffffff", font=("Helvetica", 10))
            id_label.pack()

            self.face_frames.append((frame, label))
            self.face_ids.append(int(face_id))

            frame.bind("<Button-1>", lambda event, idx=len(self.face_ids)-1: self.select_face(idx))
            label.bind("<Button-1>", lambda event, idx=len(self.face_ids)-1: self.select_face(idx))
        except Exception as e:
            logging.error(f"Error loading image {image_path}: {e}")


    def select_face(self, index):
        if self.selected_face_index is not None:
            self.face_frames[self.selected_face_index][0].configure(bg="#ffffff")

        self.selected_face_index = index
        self.face_frames[index][0].configure(bg="#e0e0ff")
        face_id = self.face_ids[index]
        logging.info(f"Selected face ID: {face_id}")

    def search_selected_face(self):
        if self.selected_face_index is None:
            messagebox.showwarning("No Selection", "Please select a face first.")
            return

        selected_face_id = self.face_ids[self.selected_face_index]
        result = search_faces_by_id(self.collection, selected_face_id)
        
        if result:
            self.show_search_results(selected_face_id, result)
        else:
            messagebox.showinfo("No Images Found", f"No images found for face ID {selected_face_id}.")

    def show_search_results(self, face_id, result):
        logging.info(f"Displaying search results for Face ID: {face_id}")

        result_window = Toplevel(self.master)
        result_window.title(f"Search Results: Face ID {face_id}")
        result_window.geometry("1000x800")
        result_window.configure(bg="#f5f5f5")

        title_label = tk.Label(result_window, text=f"Search Results: Face ID {face_id}", font=("Helvetica", 24, "bold"), bg="#f5f5f5", fg="#333333")
        title_label.pack(pady=20)

        canvas = tk.Canvas(result_window, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(result_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        scrollbar.pack(side="right", fill="y")

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(result_window, variable=progress_var, maximum=100, style="TProgressbar")
        progress_bar.pack(pady=10, padx=20, fill=tk.X)

        self.image_queue = queue.Queue()
        occurrences = result.get('occurrences', [])
        logging.info(f"Number of occurrences found: {len(occurrences)}")

        def process_images():
            for i, occurrence in enumerate(occurrences):
                filename = occurrence['filename']
                bounding_box = occurrence['bounding_box']
                image_path = os.path.join('images', filename)
                if os.path.exists(image_path):
                    logging.info(f"Processing image: {image_path}")
                    processed_image = self.process_image_with_face(image_path, bounding_box)
                    self.image_queue.put((processed_image, filename))
                    logging.info(f"Processed image: {filename} ({i + 1}/{len(occurrences)})")
                else:
                    logging.warning(f"Image file not found: {image_path}")
                progress_var.set((i + 1) / len(occurrences) * 100)

            self.image_queue.put(None)  # Signal that processing is complete
            logging.info("Image processing complete.")

        def update_ui():
            try:
                item = self.image_queue.get_nowait()
                if item is None:
                    progress_bar.pack_forget()  # Hide progress bar when done
                    logging.info("All images processed, progress bar hidden.")
                    return
                processed_image, filename = item
                self.display_processed_image(scrollable_frame, processed_image, filename)
                result_window.after(10, update_ui)
            except queue.Empty:
                result_window.after(100, update_ui)

        threading.Thread(target=process_images, daemon=True).start()
        result_window.after(100, update_ui)

    def process_image_with_face(self, image_path, bounding_box):
        try:
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            top, right, bottom, left = bounding_box
            
            draw.rectangle([left, top, right, bottom], outline="#FF4081", width=30)
            
            image.thumbnail((300, 300))
            
            return image
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")
            return None

    def display_processed_image(self, parent_frame, pil_image, filename):
        if pil_image:
            # Track the total number of processed images
            total_images = len(parent_frame.winfo_children())
            row = total_images // 3  # 3 columns per row
            column = total_images % 3

            frame = tk.Frame(parent_frame, bg="#ffffff", bd=0, highlightthickness=0)
            frame.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

            photo = ImageTk.PhotoImage(pil_image)
            label = tk.Label(frame, image=photo, bg="#ffffff")
            label.image = photo
            label.pack(pady=5)

            filename_label = tk.Label(frame, text=os.path.basename(filename), bg="#ffffff", font=("Helvetica", 10))
            filename_label.pack()


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceSearchApp(root)
    root.mainloop()