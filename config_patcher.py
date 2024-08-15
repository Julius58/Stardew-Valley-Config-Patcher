from argparse import ArgumentParser
from os import listdir
from os.path import isdir, isfile
from os.path import join as path_join

from lib.config import PatcherConfig
from lib.creation import create_patch_file
from lib.patching import patch

from lib.ui.console import ConsoleUserInterface


def argparser() -> ArgumentParser:
    argparser = ArgumentParser(
        prog="Config Patcher for Stardew Valley",
        description="This script either creates a patch file or applies all provided patches to the specified config mod or creates a new one."
    )

    argparser.add_argument("--create", action='store_true', default=False, help="Changes the mode to create a new patch file from all provided config files and existing patches.")
    argparser.add_argument("--close", action='store_true', default=False, help="Closes the script immediately after completion without waiting for user input.")

    return argparser

def get_output_dir(patcher_config: PatcherConfig, cui: ConsoleUserInterface) -> str:
    config_folders = [
        path_join(patcher_config.staging, folder)
        for folder
        in listdir(patcher_config.staging)
        if (
            patcher_config.config_mod_regex.match(folder)
            and isdir(path_join(patcher_config.staging, folder))
        )
    ]

    return cui.output_folder(config_folders)

def create_PatcherConfig(cui: ConsoleUserInterface) -> PatcherConfig:
    pc = cui.create_PatcherConfig()
    pc.save()
    return pc

def main():
    args = argparser().parse_args()

    cui = ConsoleUserInterface()
    config_filepath = PatcherConfig.filepath()
    patcher_config = PatcherConfig.from_file() if isfile(config_filepath) else create_PatcherConfig(cui)

    config_mod_path = get_output_dir(patcher_config, cui)
    
    if args.create:
        create_patch_file(config_mod_path, patcher_config, cui)
    else:
        patch(config_mod_path, patcher_config)
    
    patcher_config.save()

    if not args.close:
        _ = input("Press enter to close...")

if __name__ == "__main__":
    main()