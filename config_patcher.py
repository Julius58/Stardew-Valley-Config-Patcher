from argparse import ArgumentParser
from getpass import getpass
from json import load as json_load
from os import listdir, makedirs
from os.path import basename, isdir, isfile
from os.path import join as path_join
from re import compile as regex_compile
from re import error as RegexError
from typing import Callable

from lib.config import PatcherConfig
from lib.creation import create_patch_file
from lib.patching import patch
from Typing import SCRIPT_ROOT


def argparser() -> ArgumentParser:
    argparser = ArgumentParser(
        prog="Config Patcher for Stardew Valley",
        description="This script either creates a patch file or applies all provided patches to the specified config mod or creates a new one."
    )

    argparser.add_argument("--create", action='store_true', default=False, help="Changes the mode to creating a new patch from all provided config files and old patches.")
    argparser.add_argument("--close", action='store_true', default=False, help="Closes the script immediately after completion without waiting for user input.")

    return argparser

def _get_user_input_(prompt: str, validation_function: Callable[[str], bool], hidden: bool = False) -> str:
    input_func: Callable[[str], str] = getpass if hidden else input

    while True:
        user_input = input_func(prompt).strip()
        if validation_function(user_input):
            return user_input

def get_output_dir(patcher_config: PatcherConfig) -> str:
    config_folders = [
        path_join(patcher_config.staging, folder)
        for folder
        in listdir(patcher_config.staging)
        if (
            patcher_config.config_mod_regex.match(folder)
            and isdir(path_join(patcher_config.staging, folder))
        )
    ]
            

    lines = [
        "Select an output directory:",
        "---------------------------"
    ]

    for idx, config_folder in enumerate(config_folders):
        lines += [f"[{idx}] {basename(config_folder)}"]

    lines += ["[temp]"]
    lines += ["---------------------------"]
    lines += ["> "]

    def validate(user_input: str) -> bool:
        try:
            idx = int(user_input)
        except ValueError:
            return user_input.lower() == 'temp'
        
        return idx in range(len(config_folders))

    selection = _get_user_input_('\n'.join(lines), validate).lower()

    if selection == 'temp':
        temp_folder = path_join(SCRIPT_ROOT, 'temp')
        if not isdir(temp_folder):
            makedirs(temp_folder)
        return temp_folder
    
    return config_folders[int(selection)]

def create_PatcherConfig() -> PatcherConfig:
    def stardew_valley_validation(user_input: str) -> bool:
        if not isdir(user_input):
            return False
        
        stardew_valley_exe_path = path_join(user_input, 'Stardew Valley.exe')

        return isfile(stardew_valley_exe_path)

    def staging_validation(user_input: str) -> bool:
        if not isdir(user_input):
            return False

        staging_folder_filename = '__vortex_staging_folder'
        staging_folder_file_path = path_join(user_input, staging_folder_filename)

        if not isfile(staging_folder_file_path):
            return False
        
        with open(staging_folder_file_path, 'r') as f:
            d = json_load(f)

        return (
            isinstance(d, dict)
            and d.get('game', '') == 'stardewvalley'
        )
    
    def config_mod_regex_validation(user_input: str) -> bool:
        try:
            regex = regex_compile(user_input)
        except RegexError as re_err:
            return False
        
        confirm = input(f'<{regex.pattern}> Correct? [y]/[n]: ').strip().lower()
        return (
            len(confirm) > 0
            and confirm[0] == 'y'
        )
    
    stardew_valley = _get_user_input_("Full path to the Stardew Valley folder: ", stardew_valley_validation)
    staging = _get_user_input_("Full path to the staging folder of Vortex: ", staging_validation)
    config_mod_regex = regex_compile(_get_user_input_("Enter a valid regex pattern to search for config mod folders: ", config_mod_regex_validation))
    
    pc = PatcherConfig(
        staging=staging,
        stardew_valley=stardew_valley,
        config_mod_regex=config_mod_regex,
        patch_version=-1
    )

    pc.save()
    return pc

def main():
    args = argparser().parse_args()

    config_filepath = PatcherConfig.filepath()
    patcher_config = PatcherConfig.from_file() if isfile(config_filepath) else create_PatcherConfig()

    config_mod_path = get_output_dir(patcher_config)
    
    if args.create:
        create_patch_file(config_mod_path, patcher_config)
    else:
        patch(config_mod_path, patcher_config)
    
    patcher_config.save()

    if not args.close:
        _ = input("Press enter to close...")

if __name__ == "__main__":
    main()