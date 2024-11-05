from flask import Flask, request, jsonify, send_from_directory
import os,re
import requests
from moviepy.editor import VideoFileClip
import shutil
import threading
import time
from proglog import ProgressBarLogger


app = Flask(__name__)
DOWNLOAD_DIR = 'dl'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# To store download progress
progress = {}


def clean_dir(directory_path):
    # Check if the specified directory exists
    if not os.path.isdir(directory_path):
        print(f"Directory {directory_path} does not exist.")
        return

    # Iterate through all files and folders in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        try:
            # Check if it's a file or directory and delete accordingly
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # Remove file or symbolic link
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # Remove directory and all its contents
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")
            return jsonify({"s":0,"error": f"Failed to delete files.","reson":f"{e}"}), 400

    print(f"Directory {directory_path} cleaned successfully.")

@app.route('/clean', methods=['GET'])
def cldir():
    cl=clean_dir(DOWNLOAD_DIR)
    if cl:
        return jsonify({"s":0,"error": "err on clean"}), 400
    return return jsonify({"s":1,"error": "Directory cleaned successfully."}), 200

@app.route('/', methods=['GET'])
def hellow():
    return "hello world"


@app.route('/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({"s":0,"error": "URL parameter is required"}), 400

    filename = os.path.basename(url)
    if "?" in filename:
        filename = filename.split("?")[0]
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    optimized_path = os.path.join(DOWNLOAD_DIR, f"optimized_{filename}")
    progress[filename] = "Downloading"

    try:
        # Download the video file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
                bytes_downloaded += len(chunk)
                progress[filename] = f"Downloading: {int((bytes_downloaded / total_size) * 100)}%"

        progress[filename] = "Downloaded"
        
        # Optimize the video
        progress[filename] = "Optimizing"
        optimize_video(file_path, optimized_path,filename)
        progress[filename] = "Optimized"

        download_url = request.url_root + 'download/' + f"optimized_{filename}"
        progress[filename] = "Completed"

        return jsonify({
            "s":1,
            "status": "Completed",
            "filename": f"optimized_{filename}",
            "download_url": download_url,
            "progress": progress[filename]
        })
    except Exception as e:
        progress[filename] = "Error"
        return jsonify({"s":0,"error": str(e)}), 500

@app.route('/progress', methods=['GET'])
def get_progress():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({"s":0,"error": "Filename parameter is required"}), 400
    return jsonify({"s":0,"progress": progress.get(filename, "Not found")})

@app.route('/download/<path:filename>', methods=['GET'])
def serve_file(filename):
    print(f"Serving file: {filename}")
    return send_from_directory(DOWNLOAD_DIR, filename)



def optimize_video(input_path, output_path, filename):
    progress[filename] = {"pres":"","st":""}
    progress[filename]["pres"] = "Optimizing: 0%"
    
    class MyBarLogger(ProgressBarLogger):
      def callback(self, **changes):
        for (parameter, value) in changes.items():
            progress[filename]["st"]='Parameter %s is now %s' % (parameter, value)
            #print(progress[filename].st)
      def bars_callback(self, bar, attr, value,old_value=None):
        percentage = (value / self.bars[bar]['total']) * 100
        npr=f"Optimizing: {percentage:.2f}%"
        #print(progress[filename])
        if float(percentage) % 5 == 0:
         #print(number)  # Outpu
          progress[filename]["pres"]=npr
          print(progress[filename])
          
    
    logger = MyBarLogger()
    try:
        with VideoFileClip(input_path) as video:
            video.write_videofile(
                output_path,
                #bitrate="500k",
                preset="ultrafast",
                audio=True,
                logger=logger
            )
        progress[filename]["st"] = "Optimized"
    except Exception as e:
        progress[filename] = f"Error: {str(e)}"
        print(f"Error optimizing {filename}: {e}")
    print("Optimization complete for:", filename)



def optimize_videoo(input_path, output_path,filename):
    with VideoFileClip(input_path) as video:
       video.write_videofile(output_path, bitrate="500k", preset="ultrafast", audio=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8000,debug=False)
