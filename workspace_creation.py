import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--output_dir', help="""Subdirectory of ./output/ where the workspace are written out to""")
    parser.add_argument(
        '--input_dir', required=True, help="""Input directory where datacards are""")
    parser.add_argument(
        '--year', default='2018', help="""Year to produce datacards for (2017 or 2016)""")
    args = parser.parse_args()

    # Ensure the base output directory exists
    if args.output_dir is None:
        args.output_dir = args.input_dir
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    print('Base output directory: {}'.format(args.output_dir))

    for root, subdirs, files in os.walk(args.input_dir):
        for file in files:
            if file.endswith('.txt'):
                rel_path = os.path.relpath(root, args.input_dir)
                output_subdir = os.path.join(args.output_dir, rel_path)
                
                # Ensure the output subdirectory exists
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)

                output_file = os.path.join(output_subdir, 'workspace_{}.root'.format(file.replace('.txt', '')))
                input_file = os.path.join(root, file)
                if 'Run2_Run3' not in input_file:
                    continue
                if 'M1000_Width4' not in input_file:
                    continue
                command = f"text2workspace.py {input_file} -m 800 -o {output_file} --channel-masks" # --channel-masks

                if os.path.exists(output_file):
                    print(f"Output file {output_file} already exists. Skipping...")
                    continue

                print('Executing: {}'.format(command))
                # Using subprocess.call for compatibility with older Python versions
                return_code = subprocess.call(command, shell=True)
                if return_code == 0:
                    print("Command executed successfully!")
                else:
                    print("Command failed with return code:", return_code)

if __name__ == "__main__":
    main()
