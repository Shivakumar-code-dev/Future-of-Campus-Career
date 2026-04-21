import os

def tree_structure(folder, indent=""):
    items = os.listdir(folder)
    tree_str = ""
    for i, item in enumerate(items):
        path = os.path.join(folder, item)
        connector = "└── " if i == len(items) - 1 else "├── "
        tree_str += f"{indent}{connector}{item}\n"
        if os.path.isdir(path):
            extension = "    " if i == len(items) - 1 else "│   "
            tree_str += tree_structure(path, indent + extension)
    return tree_str

# Set your main folder (use '.' for current folder)
main_folder = '.'
output_file = 'file_structure.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"{main_folder}\n")
    f.write(tree_structure(main_folder))

print(f"Tree structure saved to {output_file}")
