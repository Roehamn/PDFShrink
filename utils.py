import os

def generate_output_filename(input_path, output_dir, quality):
    base = os.path.basename(input_path)
    name, ext = os.path.splitext(base)
    return os.path.join(output_dir, f"{name}_compressed_q{quality}{ext}")

