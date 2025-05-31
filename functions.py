import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import logger



from typing import List, Union



# Load `.py` files as string
def load_python_code(path: Union[str, List[str]]) -> str:
    
    code_blocks = []

    # Case 1: List of file paths
    if isinstance(path, list):
        file_paths = path

    # Case 2: Directory path
    elif os.path.isdir(path):
        file_paths = [
            os.path.join(root, file)
            for root, _, files in os.walk(path)
            for file in files if file.endswith(".py")
        ]

    # Case 3: Single file path
    elif os.path.isfile(path) and path.endswith(".py"):
        file_paths = [path]

    else:
        raise ValueError("Input must be a .py file, a directory, or a list of .py file paths.")

    # Read code from each file
    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_blocks.append(f"# ===== {file_path} =====\n" + f.read())
        except Exception as e:
            logger.info(f"Failed to read {file_path}: {e}")

    return "\n\n".join(code_blocks)

