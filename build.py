import os
import shutil
import sys
import configparser

# Variables
addon_name = ""
output_path = ""
create_archive = ""


# Methods
def copy_addon(src_path, dst_path):
    """
    Copies an addons source files from src_path to dst_path.
    :param src_path: The source, containing all of the python sources to copy.
    :param dst_path: The destination, a Blender addons path.
    """
    if os.path.exists(dst_path):
        print(f"{addon_name} directory exists. Deleting it.")
        shutil.rmtree(dst_path)

    shutil.copytree(src_path, dst_path)
    print("Addon copied.")


def read_config():
    """
    Reads the build config, or creates a template if one doesn't exist.
    """
    output_dir_path = os.path.join(os.getcwd(), "build_confg.ini")

    if os.path.exists(output_dir_path):
        config = configparser.ConfigParser()
        config.read(output_dir_path)

        global output_path
        output_path = config["Paths"]["Output Path"]

        global addon_name
        addon_name = config["Addon"]["Name"]

        global create_archive
        create_archive = config.getboolean("Addon", "Archive")

        if not os.path.exists(output_path):
            print("An invalid output path was provided. Please make sure the directory exists and then rebuild!")
            sys.exit()

        if not addon_name:
            print("No addon name was provided. Please make sure the addon name has characters and then rebuild!")
            sys.exit()

        print(f"Loaded config for {addon_name}, copying to {output_path}. Creating archive: {create_archive}")

        return
    else:
        config = configparser.ConfigParser()

        section_path = "Paths"
        config[section_path] = {}
        config[section_path]["Output Path"] = "Enter shared Blender addons path here."

        section_addon = "Addon"
        config[section_addon] = {}
        config[section_addon]["Name"] = os.path.basename(os.getcwd())
        config[section_addon]["Archive"] = "True"

        with open(output_dir_path, "w") as ini:
            config.write(ini)

        print("No build_output.ini file was present. One has been created, please fill it out and rebuild!")
        sys.exit()


def make_archive(addon_path):
    """
    Writes the copied addon into an archive and stores it next to the build script.
    :param addon_path: The path of the addon to archive. This is the directory containing the __init__.py file.
    """
    tmp_path = os.path.join(os.getcwd(), "tmp")
    tmp_addon_path = os.path.join(tmp_path, addon_name)
    archive_path = os.path.join(os.getcwd(), addon_name)

    shutil.copytree(addon_path, tmp_addon_path)
    shutil.make_archive(archive_path, "zip", tmp_path)

    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)


# Execution
read_config()

addon_src = os.path.join(os.getcwd(), "src")
addon_dst = os.path.join(output_path, addon_name)

copy_addon(addon_src, addon_dst)
if create_archive: make_archive(addon_dst)



