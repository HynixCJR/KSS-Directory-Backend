import os
import hashlib
import json

def load_data_file(filepath):
    '''Safely load JSON data. Returns an empty dictionary if an error occurs'''

    if os.path.isfile(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as data_file: 
                return json.load(data_file)   
        except:
            print("Error loading file: " + filepath)
    else:
        print("Error loading file: " + filepath)

    return {}
        
def dump_data_file(data, filepath):
    '''Safely write JSON data. Probably atomic, and creates the path and file automatically if either don't exist.'''
    dirpath = os.path.dirname(filepath)

    # make sure path exists
    if not os.path.exists(dirpath) and dirpath != "":
        os.makedirs(dirpath, exist_ok=True)

    with open(filepath + ".temp", "w") as data_file:
        data_file.truncate(0) # clear file
        # write to now empty file
        json.dump(data, data_file)

        # forcefully write to temporary file
        data_file.flush()
        os.fsync(data_file)

    # atomically (I hope??) replace target file
    os.replace(filepath + ".temp", filepath)

def hash_file(filepath):
    '''Safely hash a file. Returns the string 'none' if an error occurs'''

    if os.path.isfile(filepath):
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            print("Error loading file: " + filepath)
    else:
        print("Error loading file: " + filepath)

    return "none"



def dump_data_file_old(data, path, filename):
    # make sure path exists
    if not os.path.exists(path):
        os.makedirs(path)

    with open(path + "/" + filename + ".json.temp", "w") as data_file:
        data_file.truncate(0) # clear file
        # write to now empty file
        json.dump(data, data_file)

        # forcefully write to temporary file
        data_file.flush()
        os.fsync(data_file)

    # atomically (I hope??) replace target file
    os.replace(path + "/" + filename + ".json.temp", path + "/" + filename + ".json")